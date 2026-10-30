# How to Add a New Agent

1. Create a folder `src/ai_agents/agents/my_agent/` with:
   - `config.yaml`: `state_schema`, plus `workflow.entrypoint`, `workflow.nodes` (name, handler, type) and `workflow.edges` (from, to).
   - `handlers.py`: one function per handler name, `handler(state, model=None, tools=None, memory=None, node_type=None, **kwargs)`, returning the updated state dict.
   - `prompts/<handler_name>.tpl` (optional): prompt template rendered with the state.
2. In `__init__.py`, implement a class that inherits from `WorkflowAgent` (`ai_agents.agents.workflow_agent`) and sets `default_config_path`, `handler_module` and `prompt_dir` (copy `calculator/__init__.py`).
3. Add the agent to `AGENT_REGISTRY` in `src/ai_agents/agents/registry.py`.
4. Run it: `python run_cli.py my_agent --input '{"key": "value"}'`, or `POST /api/agents/my_agent/run` on the API server.

Every key a handler writes must be declared in `state_schema`: LangGraph drops undeclared keys between nodes.
