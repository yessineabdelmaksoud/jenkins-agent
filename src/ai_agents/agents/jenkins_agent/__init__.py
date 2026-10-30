import os
from typing import Any, Dict, Optional
from ai_agents.agents.workflow_agent import WorkflowAgent
from . import handlers


class JenkinsAgent(WorkflowAgent):
    """JenkinsAgent: workflow-based agent to handle Jenkins job events.

    Minimal implementation: uses workflow YAML in the same folder and handlers module.
    """

    default_config_path = os.path.join(os.path.dirname(__file__), "config.yaml")

    def __init__(self, config: Dict[str, Any], config_path: Optional[str] = None):
        self.default_config_path = config_path or self.default_config_path
        super().__init__(config)

    @property
    def handler_module(self):
        return handlers

    @property
    def prompt_dir(self):
        return os.path.join(os.path.dirname(__file__), "prompts")

    def build_model(self):
        """Return the `model:` block from config.yaml as plain settings.

        The handlers call an OpenAI-compatible endpoint (OpenRouter by default)
        with the OpenAI SDK and read the model id and base URL from this dict, so
        no LangChain model (and no API key) is needed to build the agent.
        """
        return dict(self.config.get("model") or {})

    def build_agent(self):
        return self._build_workflow_graph(self.config, self.handler_module, self.prompt_dir)
