"""The automatic-retry cap must hold across the builds the agent retriggers."""

from ai_agents.agents.jenkins_agent import handlers
from ai_agents.agents.jenkins_agent.retry_store import RetryStore


NETWORK_FAILURE = {
    "cause": "Connection timed out",
    "suggested_actions": ["Retry the build"],
    "confidence": 0.9,
    "category": "network",
}


def _failed_build_run(build_number, job="flaky-job"):
    """Run make_decision + execute_action as a fresh graph run would (retry_count not in state)."""
    state = {
        "job_name": job,
        "build_number": build_number,
        "build_status": "FAILURE",
        "jenkins_url": "http://jenkins.invalid",
        "failure_analysis": dict(NETWORK_FAILURE),
    }
    state = handlers.make_decision(state)
    return handlers.execute_action(state)


def test_retry_store_counts_persist_and_reset(tmp_path):
    path = str(tmp_path / "counts.json")
    store = RetryStore(path)
    assert store.get("job") == 0
    assert store.increment("job") == 1
    assert store.increment("job") == 2
    assert RetryStore(path).get("job") == 2  # survives a new instance / process
    assert RetryStore(path).get("other") == 0
    store.reset("job")
    assert RetryStore(path).get("job") == 0


def test_retry_store_ignores_corrupt_file(tmp_path):
    path = tmp_path / "counts.json"
    path.write_text("not json")
    store = RetryStore(str(path))
    assert store.get("job") == 0
    assert store.increment("job") == 1


def test_retries_are_capped_across_retriggered_builds(fake_tools):
    jenkins, _ = fake_tools

    first = _failed_build_run(10)
    assert first["action_taken"] == "retriggered"
    assert first["retry_count"] == 1

    # The retriggered build fails again: a new run, with fresh graph state.
    second = _failed_build_run(11)
    assert second["action_taken"] == "retriggered"
    assert second["retry_count"] == 2

    third = _failed_build_run(12)
    assert third["decision"] == "notify"
    assert "Retry limit exceeded (2/2)" in third["decision_info"]["reasoning"]
    assert third["action_taken"] == "notified"

    assert jenkins.triggered == ["flaky-job", "flaky-job"]


def test_success_resets_the_retry_budget(fake_tools):
    jenkins, _ = fake_tools
    _failed_build_run(1)
    _failed_build_run(2)
    assert _failed_build_run(3)["action_taken"] == "notified"

    handlers.analyze_status({"job_name": "flaky-job", "build_status": "SUCCESS"})

    assert _failed_build_run(4)["action_taken"] == "retriggered"
    assert len(jenkins.triggered) == 3


def test_retry_budget_is_per_job(fake_tools):
    _failed_build_run(1, job="a")
    _failed_build_run(2, job="a")
    assert _failed_build_run(3, job="a")["action_taken"] == "notified"
    assert _failed_build_run(1, job="b")["action_taken"] == "retriggered"


def test_max_retries_is_configurable(fake_tools, monkeypatch):
    monkeypatch.setenv("JENKINS_MAX_RETRIES", "1")
    assert _failed_build_run(1)["action_taken"] == "retriggered"
    assert _failed_build_run(2)["action_taken"] == "notified"


def test_failed_trigger_is_not_counted(fake_tools):
    jenkins, _ = fake_tools
    jenkins.trigger_result = False
    assert _failed_build_run(1)["action_taken"] == "retry_failed"
    assert RetryStore().get("flaky-job") == 0


def test_full_graph_retries_then_notifies(fake_tools, fake_llm):
    from ai_agents.agents.registry import get_agent

    jenkins, notifications = fake_tools
    agent = get_agent("jenkins_agent")
    payload = {"job_name": "flaky-job", "jenkins_url": "http://jenkins.invalid"}

    results = [agent.run({**payload, "build_number": n}) for n in (20, 21, 22)]

    assert [r["action_taken"] for r in results] == ["retriggered", "retriggered", "notified"]
    assert jenkins.triggered == ["flaky-job", "flaky-job"]
    # decision_info now reaches the notification step
    last = results[-1]["notification_content"]
    assert last["decision_info"]["decision"] == "notify"
    assert results[-1]["status"] == "done"

    # A green build resets the counter, so the next transient failure is retried again.
    jenkins.builds[("flaky-job", 23)] = ("SUCCESS", "Finished: SUCCESS\n" * 3)
    assert agent.run({**payload, "build_number": 23})["status"] == "done"
    assert agent.run({**payload, "build_number": 24})["action_taken"] == "retriggered"
