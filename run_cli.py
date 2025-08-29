
"""Light-weight launcher to run the package CLI without setting PYTHONPATH.

Usage:
  python run_cli.py jenkins_agent --input-file .\input.json

This script prepends the project's src/ directory to sys.path and sets PYTHONPATH
for subprocesses, then runs the module `ai_agents.execution.cli` as __main__ so
it behaves like `python -m ai_agents.execution.cli` but works even when the
package isn't installed or PYTHONPATH isn't set.
"""
import os
import sys
import runpy
from pathlib import Path

# Determine project root and src directory
REPO_ROOT = Path(__file__).resolve().parent
SRC_DIR = REPO_ROOT / "src"

# Prepend src to sys.path so imports like `import ai_agents` work
_src_str = str(SRC_DIR)
if _src_str not in sys.path:
    sys.path.insert(0, _src_str)

# Ensure PYTHONPATH includes src for subprocesses
existing = os.environ.get("PYTHONPATH", "")
if _src_str not in existing.split(os.pathsep):
    os.environ["PYTHONPATH"] = _src_str + (os.pathsep + existing if existing else "")

# Run the module as __main__ so argument parsing works normally
if __name__ == "__main__":
    # runpy.run_module will use sys.argv as provided, so forwarding CLI args works
    runpy.run_module("ai_agents.execution.cli", run_name="__main__", alter_sys=True)
