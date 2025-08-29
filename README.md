

# Ai Agents

A framework for building modular, extensible AI agents using LangGraph.

## 🎥 Demo

Watch the Jenkins Agent in action:

[![Jenkins Agent Demo](https://img.youtube.com/vi/38-cWAtA4P0/maxresdefault.jpg)](https://www.youtube.com/watch?v=38-cWAtA4P0)

*Click the image above to watch the complete Jenkins Agent workflow demonstration*

## Features

- 🤖 Build modular AI agents with clear interfaces
- 🔧 Extensible tool system
- 💾 Pluggable memory backends
- 📊 Graph-based workflow execution
- 🚀 Easy deployment options

## 📚 Documentation

- **[Jenkins Agent Guide](docs/JENKINS_AGENT.md)** - Complete guide for Jenkins build monitoring and automation
- **[Deployment Guide](docs/DEPLOYMENT.md)** - API endpoints, Docker setup, Kubernetes deployment, and configuration
- **[How to Add a New Agent](docs/how_to_add_agent.md)** - Tutorial for creating custom agents

## Quick Start

1. Install dependencies:
```bash
pip install poetry
poetry install
```

2. Set up environment variables:
```bash
cp .env.example .env
# Add your OpenAI API key to .env
```

3. Run an agent:
```bash
# CLI mode
python -m ai_agents.execution.cli sales_assistant

# API mode
python src/ai_agents/deployment/api_agent/start_api.py
```

4. Environment Setup

Create a `.env` file in the project root with the following content:

```env
PYTHONPATH=src
OPENAI_API_KEY=your-openai-api-key-here
```

Replace `your-openai-api-key-here` with your actual OpenAI API key.

The `.env` file is required for the agent to access the OpenAI API and for correct module resolution.


## Project Structure

- `ai_agents/`: Main package
  - `agents/`: Agent implementations
  - `memory/`: Memory backends
  - `model/`: LLM handling
  - `tools/`: Tool implementations
  - `workflows/`: Graph definitions
  - `execution/`: Running agents
  - `deployment/`: Deployment options
    - `api_agent/`: FastAPI REST API server

## Adding New Agents

See [How to Add a New Agent](docs/how_to_add_agent.md) for a complete tutorial on creating custom agents.

## Jenkins Agent

The framework includes a powerful Jenkins Agent for automated build monitoring and intelligent failure analysis. Key features:

- 🔍 **Automatic Build Monitoring** - Real-time Jenkins polling and webhook support
- 🧠 **AI-Powered Analysis** - LLM-based failure cause detection and suggested actions
- 🔄 **Intelligent Auto-Retry** - Smart decision making for build retries
- 📧 **Multi-Channel Notifications** - Email and Slack notifications with detailed analysis
- 🎯 **Configurable Workflows** - YAML-based workflow customization
- 🛡️ **Data Sanitization** - Automatic PII detection and removal
- 🌐 **Web Dashboard** - Real-time monitoring interface

For complete documentation, see the [Jenkins Agent Guide](docs/JENKINS_AGENT.md).

## Prompt Templates and Constructors

Each node handler can use a prompt template and/or a prompt constructor for flexible prompt generation:

- Place prompt templates as `.tpl` files in the `src/ai_agents/agents/sales_assistant/prompts/` directory, named after the handler (e.g., `start_node.tpl`).
- Optionally, define a `handler_prompt` function (e.g., `start_node_prompt`) in your handler module. This function receives both the state and the prompt template and can return a custom prompt string.
- The system will use the prompt constructor if present, otherwise it will render the template with the state.

Example prompt template (`prompts/start_node.tpl`):

```text
You are a helpful sales assistant. Answer the following customer query:

Customer: $customer_query
```

Example prompt constructor in `handlers.py`:

```python
def start_node_prompt(state, prompt_template):
    from ai_agents.workflows.core.prompts import render_prompt
    base_prompt = render_prompt(prompt_template, state) if prompt_template else ""
    return f"[SALES PROMPT] {base_prompt}"
```

This allows you to flexibly generate prompts for each step in your workflow.

## Workflow Visualization

You can visualize your workflow YAML files as graphs using the `render_graph.py` script:

```bash
python src/ai_agents/workflows/visualizer/render_graph.py path/to/your_workflow.yaml
```

This will generate a `workflow_graph.png` file in the current directory, showing the nodes and transitions in your workflow.

## API Server

The framework includes a FastAPI-based REST API server for managing and executing agents remotely.

### Starting the API Server

```bash
# Start the API server
python src/ai_agents/deployment/api_agent/start_api.py

# Test configuration
python src/ai_agents/deployment/api_agent/test_config.py
```

### Key Features

- 🚀 **RESTful API** - Complete agent management and execution
- 🔗 **Jenkins Integration** - Webhook endpoints and polling service
- 📊 **Real-time Dashboard** - Web-based monitoring interface
- 📈 **Metrics & Health Checks** - Prometheus-compatible monitoring
- 🐳 **Container Ready** - Docker and Kubernetes deployment support

### API Endpoints

- `GET /api/agents` - List all available agents
- `POST /api/agents/{agent_id}/run` - Execute an agent
- `POST /api/jenkins/webhook` - Jenkins webhook endpoint
- `GET /api/dashboard/status` - System status and metrics

### API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

For complete deployment documentation, see the [Deployment Guide](docs/DEPLOYMENT.md).

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## License
