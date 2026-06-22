"""
Semantic Drift & Abuse Harness — E-COS v0.1

Brutal, minimal probe for semantically hollow but structurally valid behavior.

Focus: Detect when valid event sequences produce degenerate, noisy, or meaningless outcomes.
This is the first step toward epistemic quality enforcement.
"""

import os
import tempfile
from collections import Counter

from ecos.core.primitives import Event, EventType, EventLog


def count_redundant_ir_nodes(events):
    ir_nodes = [e for e in events if e.type == EventType.IR_NODE_CREATED]
    node_types = [e.payload.get("node_type", "unknown") for e in ir_nodes]
    counts = Counter(node_types)
    return sum(1 for c in counts.values() if c > 1)  # number of duplicate types


def compute_state_entropy(node):
    """Very rough proxy for semantic richness of final state."""
    state = node.state
    total = 0
    for key, value in state.items():
        if isinstance(value, (list, dict)):
            total += len(value) if hasattr(value, "__len__") else 1
        else:
            total += 1
    return total


def run_drift_case(name, build_events_fn):
    print(f"\n--- {name} ---")
    with tempfile.TemporaryDirectory() as tmp:
        log = EventLog(persist_path=os.path.join(tmp, "drift.jsonl"))

        events = build_events_fn()
        for ev in events:
            try:
                log.append(ev)
            except Exception as e:
                print(f"  Rejected early: {e}")
                return

        final_node = log.reduce_to_node("main")
        redundancy = count_redundant_ir_nodes(log.events)
        entropy = compute_state_entropy(final_node)
        event_count = len(log.events)

        print(f"  Events emitted: {event_count}")
        print(f"  Redundant IR nodes: {redundancy}")
        print(f"  State entropy (rough): {entropy}")
        print(f"  Final compiler tasks: {final_node.state.get('compiler_tasks', [])}")

        # Simple degeneracy signals
        if redundancy > 2:
            print("  ⚠ HIGH REDUNDANCY detected")
        if event_count > 20 and entropy < 5:
            print("  ⚠ LOW ENTROPY despite high event volume (possible no-op convergence)")


def case_duplicate_ir_nodes():
    """Contract-compliant but semantically empty: many duplicate IR nodes."""
    events = []
    task_id = "drift_dup_001"
    events.append(Event(type=EventType.COMPILER_TASK_STARTED, payload={"task_id": task_id}, intent="start"))
    for i in range(8):
        events.append(Event(
            type=EventType.IR_NODE_CREATED,
            payload={"task_id": task_id, "node_type": "DuplicateModule", "name": f"dup_{i}"},
            intent="create_duplicate_node"
        ))
    events.append(Event(type=EventType.IR_FINALIZED, payload={"task_id": task_id}, intent="finalize"))
    events.append(Event(type=EventType.COMPILER_TASK_COMPLETED, payload={"task_id": task_id}, intent="complete"))
    return events


def case_intent_laundering():
    """Valid structure, lying intent + noop payload."""
    events = []
    task_id = "drift_launder_001"
    events.append(Event(type=EventType.COMPILER_TASK_STARTED, payload={"task_id": task_id}, intent="start"))
    events.append(Event(
        type=EventType.IR_NODE_CREATED,
        payload={"task_id": task_id, "node_type": "Noop", "name": "empty"},
        intent="create_ir_root_node"  # lying intent
    ))
    events.append(Event(type=EventType.IR_FINALIZED, payload={"task_id": task_id}, intent="finalize"))
    events.append(Event(type=EventType.COMPILER_TASK_COMPLETED, payload={"task_id": task_id}, intent="complete"))
    return events


def case_over_generation():
    """One meaningful + many redundant events."""
    events = []
    task_id = "drift_over_001"
    events.append(Event(type=EventType.COMPILER_TASK_STARTED, payload={"task_id": task_id}, intent="start"))
    events.append(Event(type=EventType.IR_NODE_CREATED, payload={"task_id": task_id, "node_type": "Root"}, intent="create_root"))
    for i in range(25):
        events.append(Event(
            type=EventType.IR_NODE_CREATED,
            payload={"task_id": task_id, "node_type": "Noise", "name": f"noise_{i}"},
            intent="create_noise"
        ))
    events.append(Event(type=EventType.IR_FINALIZED, payload={"task_id": task_id}, intent="finalize"))
    events.append(Event(type=EventType.COMPILER_TASK_COMPLETED, payload={"task_id": task_id}, intent="complete"))
    return events


def case_noop_convergence():
    """Many events that collapse to almost no state change."""
    events = []
    task_id = "drift_noop_001"
    events.append(Event(type=EventType.COMPILER_TASK_STARTED, payload={"task_id": task_id}, intent="start"))
    for i in range(40):
        events.append(Event(
            type=EventType.LOWERING_STEP,
            payload={"task_id": task_id, "step": "noop", "index": i},
            intent="noop_step"
        ))
    events.append(Event(type=EventType.IR_FINALIZED, payload={"task_id": task_id}, intent="finalize"))
    events.append(Event(type=EventType.COMPILER_TASK_COMPLETED, payload={"task_id": task_id}, intent="complete"))
    return events


def main():
    print("=" * 72)
    print("SEMANTIC DRIFT & ABUSE HARNESS — Detecting hollow but valid behavior")
    print("=" * 72)

    run_drift_case("Duplicate IR nodes (redundancy attack)", case_duplicate_ir_nodes)
    run_drift_case("Intent laundering + noop payload", case_intent_laundering)
    run_drift_case("Over-generation of redundant nodes", case_over_generation)
    run_drift_case("No-op convergence (high volume, low meaning)", case_noop_convergence)

    print("\n" + "=" * 72)
    print("Drift harness complete. These are the patterns that will degrade CEOS projections.")
    print("=" * 72)


if __name__ == "__main__":
    main()
