"""Tests for the YAML -> LangGraph graph builder in WorkflowAgent."""

import types

from ai_agents.agents.workflow_agent import WorkflowAgent


def _record(name, next_node=None):
    def handler(state, **kwargs):
        visited = list(state.get("visited") or []) + [name]
        update = {**state, "visited": visited}
        if next_node:
            update["next_node"] = next_node
        return update

    return handler


def _make_agent(cfg, handlers):
    module = types.SimpleNamespace(**handlers)

    class _Agent(WorkflowAgent):
        handler_module = module
        prompt_dir = "/nonexistent"

    return _Agent(cfg)


STATE_SCHEMA = {"visited": "array", "next_node": "string", "error": "string"}


def _linear_config(error_node="handle_error"):
    workflow = {
        "entrypoint": "first",
        "nodes": [
            {"name": "first", "handler": "first"},
            {"name": "second", "handler": "second"},
            {"name": "third", "handler": "third"},
            {"name": "handle_error", "handler": "handle_error"},
        ],
        "edges": [
            {"from": "first", "to": "second"},
            {"from": "second", "to": "third"},
        ],
    }
    if error_node is not None:
        workflow["error_node"] = error_node
    return {"state_schema": STATE_SCHEMA, "workflow": workflow}


def test_static_edges_run_in_order_without_errors():
    agent = _make_agent(
        _linear_config(),
        {
            "first": _record("first"),
            "second": _record("second"),
            "third": _record("third"),
            "handle_error": _record("handle_error"),
        },
    )
    result = agent.run({"visited": []})
    assert result["visited"] == ["first", "second", "third"]


def test_error_from_static_node_routes_to_error_node():
    def failing(state, **kwargs):
        return {
            **state,
            "visited": state["visited"] + ["first"],
            "error": "boom",
            "next_node": "handle_error",
        }

    agent = _make_agent(
        _linear_config(),
        {
            "first": failing,
            "second": _record("second"),
            "third": _record("third"),
            "handle_error": _record("handle_error"),
        },
    )
    result = agent.run({"visited": []})
    assert result["visited"] == ["first", "handle_error"]
    assert result["error"] == "boom"


def test_error_node_defaults_to_handle_error():
    agent = _make_agent(
        _linear_config(error_node=None),
        {
            "first": _record("first"),
            "second": _record("second", next_node="handle_error"),
            "third": _record("third"),
            "handle_error": _record("handle_error"),
        },
    )
    result = agent.run({"visited": []})
    assert result["visited"] == ["first", "second", "handle_error"]


def test_missing_error_node_keeps_plain_static_edges():
    cfg = _linear_config(error_node="error_handler")  # declared but not a node
    cfg["workflow"]["nodes"] = [n for n in cfg["workflow"]["nodes"] if n["name"] != "handle_error"]
    agent = _make_agent(
        cfg,
        {
            "first": _record("first", next_node="handle_error"),
            "second": _record("second"),
            "third": _record("third"),
        },
    )
    result = agent.run({"visited": []})
    assert result["visited"] == ["first", "second", "third"]


def test_conditional_node_routes_on_next_node():
    cfg = {
        "state_schema": STATE_SCHEMA,
        "workflow": {
            "entrypoint": "router",
            "nodes": [
                {"name": "router", "handler": "router", "transitions": {"conditional": True}},
                {"name": "left", "handler": "left"},
                {"name": "right", "handler": "right"},
                {"name": "end_process", "handler": "end_process"},
            ],
            "edges": [],
        },
    }
    handlers = {
        "router": _record("router", next_node="right"),
        "left": _record("left"),
        "right": _record("right"),
        "end_process": _record("end_process"),
    }
    assert _make_agent(cfg, handlers).run({"visited": []})["visited"] == ["router", "right"]

    handlers["router"] = _record("router", next_node="nowhere")
    assert _make_agent(cfg, handlers).run({"visited": []})["visited"] == [
        "router",
        "end_process",
    ]


def test_jenkins_agent_stops_at_handle_error_when_extraction_fails(monkeypatch):
    from ai_agents.agents.jenkins_agent import handlers as jenkins_handlers
    from ai_agents.agents.registry import get_agent

    called = []
    monkeypatch.setattr(
        jenkins_handlers,
        "send_notifications",
        lambda state, **kw: called.append("send_notifications") or state,
    )
    agent = get_agent("jenkins_agent")
    # No JENKINS_URL anywhere: extract_job_data sets next_node=handle_error.
    result = agent.run({"job_name": "demo", "build_number": 7})

    assert result["error"] == "Missing jenkins_url or job_name"
    assert "notification_content" not in result
    assert called == []
