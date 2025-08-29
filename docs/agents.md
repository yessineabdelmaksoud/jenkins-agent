# Agents Overview

Agents are LangGraph-driven, modular AI systems.
Each agent:

- Inherits from `BaseAgent`
- Implements `build_graph()` and `run()`
- Can use tools, memory, models
- Registers in `registry.py`
