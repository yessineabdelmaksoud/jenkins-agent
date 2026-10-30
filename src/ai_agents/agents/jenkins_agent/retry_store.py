"""Per-job counter of consecutive automatic retries, persisted across agent runs.

Each retriggered build is analysed by a fresh graph run, so a counter kept in the
graph state always starts at 0. This store keeps the count in a small JSON file
instead: it is incremented each time the agent retriggers a job and reset when
that job builds successfully, which caps automatic retries per failure streak.

The file lives in ``$JENKINS_AGENT_STATE_DIR/retry_counts.json`` (default
``.jenkins_agent/`` in the working directory). It is safe for several threads of
one process; several processes or hosts would need a shared backend.
"""

import json
import os
import tempfile
import threading
from typing import Dict, Optional


DEFAULT_STATE_DIR = ".jenkins_agent"
FILE_NAME = "retry_counts.json"

_lock = threading.Lock()


def default_path() -> str:
    """Return the store path, honouring JENKINS_AGENT_STATE_DIR."""
    state_dir = os.getenv("JENKINS_AGENT_STATE_DIR") or DEFAULT_STATE_DIR
    return os.path.join(state_dir, FILE_NAME)


class RetryStore:
    """JSON-file backed mapping of job name -> consecutive automatic retries."""

    def __init__(self, path: Optional[str] = None):
        self.path = path or default_path()

    def _read(self) -> Dict[str, int]:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
        if not isinstance(data, dict):
            return {}
        return {str(k): int(v) for k, v in data.items() if isinstance(v, int)}

    def _write(self, data: Dict[str, int]) -> None:
        directory = os.path.dirname(self.path) or "."
        os.makedirs(directory, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".retry_counts.")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, sort_keys=True)
            os.replace(tmp_path, self.path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    def get(self, job_name: str) -> int:
        """Return the number of automatic retries since the job's last success."""
        with _lock:
            return self._read().get(job_name, 0)

    def increment(self, job_name: str) -> int:
        """Record one more automatic retry for the job and return the new count."""
        with _lock:
            data = self._read()
            data[job_name] = data.get(job_name, 0) + 1
            self._write(data)
            return data[job_name]

    def reset(self, job_name: str) -> None:
        """Forget the job's retries (called when the job builds successfully)."""
        with _lock:
            data = self._read()
            if job_name in data:
                del data[job_name]
                self._write(data)
