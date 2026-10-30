"""The Jenkins handlers must use the agent's configured model and either API key."""

import copy
import sys

import pytest

from ai_agents.agents.jenkins_agent import JenkinsAgent, handlers
from ai_agents.execution import cli


FAILED_BUILD = {
    "job_name": "app",
    "build_number": 3,
    "build_status": "FAILURE",
    "jenkins_logs": "ERROR: Connection timed out\n",
}


def _agent_with_model(model_cfg):
    config = copy.deepcopy(JenkinsAgent.load_config())
    if model_cfg is None:
        config.pop("model", None)
    else:
        config["model"] = model_cfg
    return JenkinsAgent(config)


def test_shipped_config_keeps_previous_default_model(fake_llm):
    agent = _agent_with_model(copy.deepcopy(JenkinsAgent.load_config())["model"])
    handlers.handle_failure(dict(FAILED_BUILD), model=agent.model)
    assert fake_llm.calls[-1]["model"] == "openai/gpt-3.5-turbo"
    assert fake_llm.inits[-1]["base_url"] == "https://openrouter.ai/api/v1"


def test_handlers_use_configured_model_and_base_url(fake_llm):
    agent = _agent_with_model(
        {
            "type": "openai",
            "model_id": "gpt-4o-mini",
            "config": {"openai_api_base": "https://llm.example.invalid/v1"},
        }
    )
    result = handlers.handle_failure(dict(FAILED_BUILD), model=agent.model)
    assert fake_llm.calls[-1]["model"] == "gpt-4o-mini"
    assert fake_llm.inits[-1]["base_url"] == "https://llm.example.invalid/v1"
    assert result["failure_analysis"]["category"] == "network"

    handlers.handle_success(
        {"job_name": "app", "jenkinsfile_content": "pipeline { agent any }"}, model=agent.model
    )
    assert fake_llm.calls[-1]["model"] == "gpt-4o-mini"


def test_env_base_url_still_overrides_config(fake_llm, monkeypatch):
    monkeypatch.setenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    agent = _agent_with_model({"model_id": "gpt-4o-mini"})
    handlers.handle_failure(dict(FAILED_BUILD), model=agent.model)
    assert fake_llm.inits[-1]["base_url"] == "https://api.openai.com/v1"


def test_missing_model_block_falls_back_to_default(fake_llm):
    agent = _agent_with_model(None)
    assert agent.model == {}
    handlers.handle_failure(dict(FAILED_BUILD), model=agent.model)
    assert fake_llm.calls[-1]["model"] == "openai/gpt-3.5-turbo"


def test_whole_graph_uses_configured_model(fake_tools, fake_llm):
    agent = _agent_with_model({"model_id": "anthropic/claude-test"})
    agent.run({"job_name": "app", "build_number": 1, "jenkins_url": "http://jenkins.invalid"})
    assert fake_llm.calls and {c["model"] for c in fake_llm.calls} == {"anthropic/claude-test"}


def _run_cli(monkeypatch, argv):
    monkeypatch.setattr(sys, "argv", ["run_cli.py", *argv])
    return cli.main()


@pytest.mark.parametrize("key_name", ["OPENAI_API_KEY", "OPENROUTER_API_KEY"])
def test_cli_accepts_either_api_key(monkeypatch, key_name):
    monkeypatch.setenv(key_name, "test-key-not-real")
    result = _run_cli(monkeypatch, ["calculator", "--input", '{"expression": "2 + 3"}'])
    assert result["calculation_result"] == 5


def test_cli_requires_an_api_key(monkeypatch, capsys):
    with pytest.raises(SystemExit) as exc:
        _run_cli(monkeypatch, ["calculator", "--input", '{"expression": "2 + 3"}'])
    assert exc.value.code == 1
    assert "OPENROUTER_API_KEY" in capsys.readouterr().out
