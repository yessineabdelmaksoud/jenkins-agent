"""Implementation of workflow-based agents."""

from typing import Any, Dict, Optional, TypedDict
from langgraph.graph import END, StateGraph
from ai_agents.utils.config_loader import load_yaml_config
from .agent_base import AgentBase


class WorkflowAgent(AgentBase):
    """Base class for workflow-based agents using LangGraph workflows.

    Implements the AgentBase interface for agents defined through workflow YAML files
    that specify nodes and edges for the agent's behavior graph.

    Attributes:
        default_config_path: Path to the default workflow config file.
    """

    default_config_path: Optional[str] = None

    def __init__(self, config: Dict[str, Any]):
        """Initialize the workflow agent with configuration.

        Args:
            config: Dictionary containing workflow configuration including state schema,
                   memory settings, and workflow definition.
        """
        self.config = config
        self.state_schema = self.config.get("state_schema")
        self.state_typed_dict = self.build_state()
        self.memory = self.build_memory()
        self.tools = self.build_tools()
        self.model = self.build_model()
        self.graph = self.build_agent()

    @property
    def handler_module(self):
        """Get the module containing workflow handlers.

        Returns:
            Module object containing the agent's workflow handlers.
        """
        raise NotImplementedError

    @property
    def prompt_dir(self):
        """Get the directory containing prompt templates.

        Returns:
            String path to the directory containing prompt templates.
        """
        raise NotImplementedError

    def build_state(self):
        """
        Dynamically create a TypedDict class for the agent's state schema.

        Returns the TypedDict class or None if no schema.
        """
        schema = self.state_schema
        if not schema or not isinstance(schema, dict):
            return None
        # Map string type names to Python types
        type_map = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "object": dict,
            "array": list,
        }
        annotations = {}
        for k, v in schema.items():
            t = v if isinstance(v, str) else v.get("type", "any")
            annotations[k] = type_map.get(t, Any)
        return TypedDict("StateSchema", annotations)

    def build_tools(self) -> Dict[str, Any]:
        """Build and configure agent tools.

        Returns:
            Dict[str, Any]: Dictionary mapping tool names to tool instances.
        """
        return {}

    def build_memory(self) -> Optional[Any]:
        """Build agent memory system based on configuration.

        Returns:
            Optional[Any]: Memory instance if configured in self.config["memory"],
            None if memory is not configured or type is not specified.
        """
        memory_cfg = self.config.get("memory", {})
        if memory_cfg and "type" in memory_cfg:
            from ai_agents.memory.factory import MemoryFactory

            return MemoryFactory.create(
                memory_cfg["type"], memory_cfg.get("config", {})
            )
        return None

    def build_agent(self) -> StateGraph:
        """Build and return the agent's workflow graph implementation.

        Returns:
            StateGraph: The configured workflow graph for this agent.
        """
        return self._build_workflow_graph(
            self.config, self.handler_module, self.prompt_dir
        )

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the workflow with input data.

        Args:
            input_data: Dictionary containing input data for the workflow.

        Returns:
            Dict[str, Any]: The final state after workflow execution.

        Raises:
            ValueError: If input_data is not a dictionary.
        """
        if not isinstance(input_data, dict):
            raise ValueError("Input data must be a dictionary")
        return self.graph.invoke(input_data)

    @classmethod
    def load_config(cls, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load workflow configuration from YAML file.

        Args:
            config_path: Path to the YAML config file. If None, uses cls.default_config_path.

        Returns:
            Dict[str, Any]: The parsed configuration dictionary.

        Raises:
            ValueError: If no config path is provided and no default_config_path is set.
        """
        path = config_path or cls.default_config_path
        if not path:
            raise ValueError("No config path provided and no default_config_path set")
        return load_yaml_config(path)

    def _build_workflow_graph(
        self, cfg: Dict[str, Any], handler_module: Any, prompt_dir: str
    ) -> StateGraph:
        """Build workflow graph from config.

        Args:
            cfg: The workflow configuration dictionary
            handler_module: Module containing handler functions
            prompt_dir: Path to directory containing prompt templates

        Returns:
            StateGraph: The constructed workflow graph
        """
        # Implementation moved from old BaseAgent
        from ai_agents.workflows.core import handlers as core_handlers
        from ai_agents.workflows.utils.handlers_utils import (
            resolve_handler,
            handler_with_context,
        )
        from ai_agents.workflows.utils.prompts_utils import load_prompt_template
        from ai_agents.workflows.utils.node_types_utils import get_node_type

        state_type = (
            self.state_typed_dict
            if self.state_typed_dict is not None
            else self.state_schema
        )
        g = StateGraph(state_type)

        for node in cfg["workflow"]["nodes"]:
            handler_name = node["handler"]
            handler_fn = resolve_handler(handler_name, handler_module, core_handlers)
            node_name = node["name"]
            prompt_template = load_prompt_template(prompt_dir, handler_name)
            prompt_constructor = getattr(handler_module, f"{handler_name}_prompt", None)
            node_type = get_node_type(node)

            g.add_node(
                node_name,
                (
                    lambda state,
                    handler_fn=handler_fn,
                    model=self.model,
                    tools=self.tools,
                    memory=self.memory,
                    prompt_template=prompt_template,
                    prompt_constructor=prompt_constructor,
                    node_type=node_type: handler_with_context(
                        state=state,
                        handler_fn=handler_fn,
                        model=self.model,
                        tools=self.tools,
                        memory=self.memory,
                        prompt_template=prompt_template,
                        prompt_constructor=prompt_constructor,
                        node_type=node_type,
                    )
                ),
            )

        g.set_entry_point(cfg["workflow"]["entrypoint"])

        node_names = {node["name"] for node in cfg["workflow"]["nodes"]}
        # Handlers signal failures by setting next_node to the error node.
        # Only honoured when that node exists in the workflow.
        error_node = cfg["workflow"].get("error_node", "handle_error")
        if error_node not in node_names:
            error_node = None
        default_node = "end_process" if "end_process" in node_names else END

        # Add static edges, grouped by source node
        targets_by_source: Dict[str, list] = {}
        for edge in cfg["workflow"].get("edges", []):
            targets_by_source.setdefault(edge["from"], []).append(edge["to"])

        for source, targets in targets_by_source.items():
            if error_node and len(targets) == 1 and source != error_node:
                # Single successor: still divert to the error node when the
                # handler asked for it, instead of running the next node.
                target = targets[0]
                g.add_conditional_edges(
                    source,
                    lambda state, target=target: (
                        error_node
                        if state.get("next_node") == error_node
                        else target
                    ),
                    {target: target, error_node: error_node},
                )
            else:
                for target in targets:
                    g.add_edge(source, target)

        # Add conditional edges for nodes marked with conditional transitions:
        # route to the node named in next_node, or to end_process/END otherwise.
        for node in cfg["workflow"]["nodes"]:
            transitions = node.get("transitions", {})
            if transitions.get("conditional"):
                path_map = {name: name for name in node_names}
                path_map[default_node] = default_node
                g.add_conditional_edges(
                    node["name"],
                    lambda state: (
                        state.get("next_node")
                        if state.get("next_node") in node_names
                        else default_node
                    ),
                    path_map,
                )

        return g.compile()
