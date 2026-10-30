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
def offline_env(monkeypatch):
    """Unset credentials/endpoints so no test can reach Jenkins, an LLM or SMTP/Slack."""
    for name in _EXTERNAL_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    yield
