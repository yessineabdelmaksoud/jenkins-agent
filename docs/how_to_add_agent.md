# How to Add a New Agent

1. Create a new file in `agents/` like `my_agent.py`.
2. Implement a class that inherits from `BaseAgent`.
3. Add the agent to `agents/registry.py`.
4. Define its workflow using `workflows/builder.py` or YAML.
5. Use `execution/cli.py` to run it: `python cli.py --agent my_agent`.
