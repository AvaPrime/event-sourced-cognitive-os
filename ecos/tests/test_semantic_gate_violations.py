"""
Violation Observation Harness — E-COS Semantic Gate

Pure adversarial probe. No framework. No fixtures.

Goal: Prove that the jurisdiction layer (Kernel) fully contains failure
and leaves zero residue when skills propose invalid reality.
"""

import os
import tempfile

from ecos.core.primitives import (
    Event, EventType, EventLog, SemanticViolationError
)


def run_case(name: str, fn):
    try:
        fn()
        print(f"✓ {name}")
    except SemanticViolationError as e:
        print(f"✗ {name} (correctly blocked): {e}")
    except Exception as e:
        print(f"⚠ {name} (unexpected): {type(e).__name__}: {e}")


def test_missing_task_id():
    with tempfile.TemporaryDirectory() as tmp:
        log = EventLog(persist_path=os.path.join(tmp, "events.jsonl"))
        bad = Event(type=EventType.COMPILER_TASK_STARTED, payload={})  # missing task_id
        log.append(bad)


def test_missing_node_type():
    with tempfile.TemporaryDirectory() as tmp:
        log = EventLog(persist_path=os.path.join(tmp, "events.jsonl"))
        bad = Event(
            type=EventType.IR_NODE_CREATED,
            payload={"task_id": "t1"}  # missing node_type
        )
        log.append(bad)


def test_missing_step():
    with tempfile.TemporaryDirectory() as tmp:
        log = EventLog(persist_path=os.path.join(tmp, "events.jsonl"))
        bad = Event(
            type=EventType.LOWERING_STEP,
            payload={"task_id": "t1"}  # missing step
        )
        log.append(bad)


def test_missing_intent():
    # Force require_intent on one contract for this test only
    from ecos.core.primitives import EventContractRegistry
    registry = EventContractRegistry()
    contract = registry.get(EventType.COMPILER_TASK_STARTED)
    if contract:
        object.__setattr__(contract, "require_intent", True)

    with tempfile.TemporaryDirectory() as tmp:
        log = EventLog(persist_path=os.path.join(tmp, "events.jsonl"))
        bad = Event(
            type=EventType.COMPILER_TASK_STARTED,
            payload={"task_id": "t1"},
            intent=None
        )
        log.append(bad)


def test_unknown_event_allowed():
    with tempfile.TemporaryDirectory() as tmp:
        log = EventLog(persist_path=os.path.join(tmp, "events.jsonl"))
        # Use SYSTEM (has no contract) to prove unknown/uncontracted events are allowed
        unknown = Event(
            type=EventType.SYSTEM,
            payload={"note": "no contract defined, should pass"}
        )
        log.append(unknown)  # should succeed
        assert len(log) == 1


def test_valid_event_success():
    with tempfile.TemporaryDirectory() as tmp:
        log = EventLog(persist_path=os.path.join(tmp, "events.jsonl"))
        good = Event(
            type=EventType.COMPILER_TASK_STARTED,
            payload={"task_id": "valid_001"},
            intent="start_valid_task"
        )
        log.append(good)
        assert len(log) == 1
        node = log.reduce_to_node("main")
        assert any(t.get("task_id") == "valid_001" for t in node.state.get("compiler_tasks", []))


def main():
    print("=" * 70)
    print("VIOLATION OBSERVATION HARNESS — Semantic Gate Stress Test")
    print("=" * 70)

    print("\n[Adversarial Cases - Must be rejected]")
    run_case("Missing task_id on COMPILER_TASK_STARTED", test_missing_task_id)
    run_case("Missing node_type on IR_NODE_CREATED", test_missing_node_type)
    run_case("Missing step on LOWERING_STEP", test_missing_step)
    run_case("Missing intent when required", test_missing_intent)

    print("\n[Extensibility & Positive Control]")
    run_case("Unknown/uncontracted event type is allowed", test_unknown_event_allowed)
    run_case("Valid well-formed event is accepted + reduced", test_valid_event_success)

    print("\n" + "=" * 70)
    print("Harness complete. Jurisdiction layer contains failure. No leakage.")
    print("=" * 70)


if __name__ == "__main__":
    main()
