"""Shared fixtures: keep tests offline and independent of the developer's environment."""

import pytest


_EXTERNAL_ENV_VARS = [
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "OPENAI_API_BASE",
    "OPENROUTER_BASE_URL",
    "JENKINS_URL",
    "JENKINS_USER",
    "JENKINS_TOKEN",
    "EMAIL_SENDER",
    "EMAIL_PASSWORD",
    "EMAIL_TO",
    "SLACK_WEBHOOK_URL",
]


@pytest.fixture(autouse=True)
def offline_env(monkeypatch, tmp_path):
    """Unset credentials/endpoints so no test can reach Jenkins, an LLM or SMTP/Slack."""
    for name in _EXTERNAL_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("JENKINS_MAX_RETRIES", raising=False)
    # Keep each test's persisted retry counters in its own directory.
    monkeypatch.setenv("JENKINS_AGENT_STATE_DIR", str(tmp_path / "agent_state"))
    # Never pick up a developer's local .env during tests.
    from ai_agents.utils import config_loader

    monkeypatch.setattr(config_loader, "load_dotenv", lambda *args, **kwargs: False)
    yield


class FakeJenkinsTool:
    """Stands in for the "jenkins" tool: canned build data, records retriggers."""

    builds = {}
    triggered = []
    trigger_result = True

    def extract_complete_data(self, jenkins_url, job_name, build_number, *args, **kwargs):
        status, log = self.builds.get(
            (job_name, build_number), ("FAILURE", "ERROR: Connection timed out\n" * 3)
        )
        return {
            "status": status,
            "console_log": log,
            "jenkinsfile": "pipeline { agent any }",
            "metadata": {"job": job_name, "build": build_number},
        }

    def trigger_build(self, job_name, jenkins_url=None, username=None, api_token=None, params=None):
        type(self).triggered.append(job_name)
        return type(self).trigger_result


class FakeNotificationsTool:
    """Stands in for the "notifications" tool and records what would be sent."""

    sent = []

    def send_email(self, cfg, content):
        type(self).sent.append(("email", content))

    def send_slack(self, webhook, content):
        type(self).sent.append(("slack", content))


@pytest.fixture
def fake_tools(monkeypatch):
    """Route ToolRegistry lookups for jenkins/notifications to in-memory fakes."""
    from ai_agents.tools import ToolRegistry

    FakeJenkinsTool.builds = {}
    FakeJenkinsTool.triggered = []
    FakeJenkinsTool.trigger_result = True
    FakeNotificationsTool.sent = []
    real_get_tool = ToolRegistry.get_tool.__func__
    fakes = {"jenkins": FakeJenkinsTool, "notifications": FakeNotificationsTool}
    monkeypatch.setattr(
        ToolRegistry,
        "get_tool",
        classmethod(lambda cls, name: fakes.get(name) or real_get_tool(cls, name)),
    )
    return FakeJenkinsTool, FakeNotificationsTool


class _FakeCompletions:
    def __init__(self, owner):
        self.owner = owner

    def create(self, **kwargs):
        type(self.owner).calls.append(kwargs)
        message = type("Message", (), {"content": type(self.owner).response})()
        choice = type("Choice", (), {"message": message})()
        return type("Completion", (), {"choices": [choice]})()


class FakeOpenAI:
    """Stands in for openai.OpenAI: records requests, returns a canned JSON answer."""

    calls = []
    inits = []
    response = (
        '{"cause": "Connection timed out while downloading dependencies", '
        '"suggested_actions": ["Retry the build"], "confidence": 0.9, "category": "network"}'
    )

    def __init__(self, base_url=None, api_key=None, **kwargs):
        type(self).inits.append({"base_url": base_url})
        self.chat = type("Chat", (), {"completions": _FakeCompletions(self)})()


@pytest.fixture
def fake_llm(monkeypatch):
    """Replace the OpenAI client used by the Jenkins handlers; set a dummy key."""
    from ai_agents.agents.jenkins_agent import handlers

    FakeOpenAI.calls = []
    FakeOpenAI.inits = []
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-real")
    monkeypatch.setattr(handlers, "OpenAI", FakeOpenAI)
    return FakeOpenAI
