"""CLI for Running AI Agents."""

import argparse
import sys
from typing import Dict, Any
import os
from pathlib import Path
# Ensure the project's `src/` directory is on sys.path so the CLI works without setting PYTHONPATH manually.
try:
    _src_dir = Path(__file__).resolve().parents[2]  # src/ (file is src/ai_agents/execution/cli.py)
    _src_str = str(_src_dir)
    if _src_str not in sys.path:
        sys.path.insert(0, _src_str)
    # Also set PYTHONPATH in the environment for subprocesses
    existing = os.environ.get('PYTHONPATH', '')
    if _src_str not in existing.split(os.pathsep):
        os.environ['PYTHONPATH'] = _src_str + (os.pathsep + existing if existing else '')
except Exception:
    # Best-effort only; do not crash CLI if this fails
    pass

from ai_agents.agents.registry import get_agent
from ai_agents.utils.config_loader import load_env_vars
from ai_agents.utils.json_utils import load_json_string
from ai_agents.execution.runner import run_agent


def parse_args():
    """Parse command line arguments for the CLI.

    Returns:
        argparse.Namespace: Parsed command line arguments.
    """
    parser = argparse.ArgumentParser(description="Run an AI agent")
    parser.add_argument("agent", help="Name of the agent to run")
    parser.add_argument("--config", help="Path to agent config file")
    parser.add_argument("--input", help="Input data as JSON string")
    parser.add_argument("--input-file", help="Path to a JSON file containing input data")
    return parser.parse_args()


def main() -> Dict[str, Any]:
    """
    CLI entry point for running agents.

    Returns:
        dict: Agent execution results
    """
    args = parse_args()

    # Load environment variables
    env_vars = load_env_vars()
    if not (env_vars.get("OPENAI_API_KEY") or env_vars.get("OPENROUTER_API_KEY")):
        print("Error: set OPENAI_API_KEY or OPENROUTER_API_KEY (environment or .env)")
        sys.exit(1)

    try:
        # Instantiate the agent using the registry
        agent = get_agent(args.agent, args.config)

        # Parse input data
        input_data = {}
        # Prefer input file when provided (avoids PowerShell quoting issues)
        if getattr(args, 'input_file', None):
            try:
                with open(args.input_file, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                input_data = load_json_string(file_content)
            except FileNotFoundError:
                print(f"Error: input file not found: {args.input_file}")
                sys.exit(1)
            except Exception as e:
                print(f"Error parsing input file: {e}")
                sys.exit(1)
        elif args.input:
            input_data = load_json_string(args.input)

        # Execute agent using the shared runner
        results = run_agent(agent, input_data)
        return results
    except Exception as e:
        print(f"Error running agent: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    results = main()
    print(results)
