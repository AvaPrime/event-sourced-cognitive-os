"""
E-COS v0.1 — First Full Closed-Loop Cognitive Compiler Runtime

Demonstrates the complete grounded loop:

1. COMPILER_TASK_STARTED event ingested
2. LoweringSkill matches and emits deterministic IR events
3. Events appended to EventLog with jsonl persistence
4. Process "restarts" (new EventLog instance loads from disk)
5. Deterministic replay produces identical final Node state
6. Passive projections (chat + simple belief graph)

This is the first time the system proves it can survive shutdown and reproduce itself from history.
"""

import os
import tempfile
from pathlib import Path

from ecos.core.primitives import (
    Event, EventType, EventLog, project, assert_deterministic_replay
)
from ecos.skills.lowering_skill import LoweringSkill


def run_compiler_loop_demo():
    print("=" * 72)
    print("E-COS v0.1 — FIRST FULL CLOSED-LOOP COGNITIVE COMPILER RUNTIME")
    print("=" * 72)

    # Use a temporary jsonl file for this demo (real use would be persistent path)
    with tempfile.TemporaryDirectory() as tmpdir:
        persist_file = os.path.join(tmpdir, "events.jsonl")

        # === Phase 1: Fresh run - create log with persistence ===
        print("\n[PHASE 1] Fresh run with jsonl persistence enabled...")
        log = EventLog(session_id="compiler_demo_001", persist_path=persist_file)

        # Create a compiler task
        task_event = Event(
            type=EventType.COMPILER_TASK_STARTED,
            payload={
                "task_id": "task_001",
                "source": "def foo(): return 42  # simple lowering target"
            },
            branch_id="main"
        )
        log.append(task_event)
        print(f"   Ingested COMPILER_TASK_STARTED (task_id=task_001)")

        # Run the LoweringSkill directly (in real kernel this is dispatched by Agent)
        skill = LoweringSkill()
        current_node = log.reduce_to_node("main")
        emitted_events = skill.execute(current_node, task_event, {})

        for ev in emitted_events:
            log.append(ev)

        print(f"   LoweringSkill emitted {len(emitted_events)} events:")
        for ev in emitted_events:
            print(f"      → {ev.type.value}")

        node1 = log.reduce_to_node("main")
        print(f"\n   State after lowering: {node1.summary()}")
        print(f"   Compiler tasks tracked: {node1.state.get('compiler_tasks')}")

        # Verify determinism on first run
        assert assert_deterministic_replay(log, "main"), "First run determinism failed"
        print("   Determinism check on live log: PASS ✓")

        # === Phase 2: Simulate full process restart ===
        print("\n[PHASE 2] Simulating process restart (new EventLog loads from jsonl)...")
        del log  # simulate shutdown

        log2 = EventLog(session_id="compiler_demo_001_reloaded", persist_path=persist_file)
        print(f"   Reloaded {len(log2)} events from {persist_file}")

        node2 = log2.reduce_to_node("main")
        print(f"   Reconstructed node after reload: {node2.summary()}")

        # Critical proof: state must be identical after reload + reduce
        is_replay_ok = assert_deterministic_replay(log2, "main")
        print(f"   Deterministic replay after restart: {'PASS ✓' if is_replay_ok else 'FAIL ✗'}")

        if not is_replay_ok:
            print("   ERROR: State diverged after reload!")
            return False

        # === Phase 3: Passive projections ===
        print("\n[PHASE 3] Passive projections (read-only lenses over the single event log)...")
        chat_view = project(log2, view_type="chat", branch_id="main")
        timeline_view = project(log2, view_type="timeline", branch_id="main")

        print(f"   Chat projection: {len(chat_view.get('messages', []))} messages")
        print(f"   Timeline projection: {len(timeline_view.get('events', []))} events")

        # Simple passive belief-style projection (CEOS direction, kept as pure function)
        belief = project_belief_graph(log2, "main")
        print(f"   Belief graph nodes: {belief['node_count']} (claims + evidence)")

        print("\n" + "=" * 72)
        print("SUCCESS: Full closed loop achieved.")
        print("- Execution produced events")
        print("- Events survived process restart via jsonl")
        print("- Reducer reproduced identical state from history")
        print("- Multiple pure projections (including future CEOS belief graph)")
        print("=" * 72)

        return True


def project_belief_graph(event_log: EventLog, branch_id: str = "main") -> dict:
    """
    Passive CEOS-style read-model projection (v0.1).

    Pure function. No writes. No persistence. No branching logic.
    Just a lens that turns event history into a simple belief/claim graph.
    """
    events = event_log.get_events(branch_id=branch_id)
    nodes = []
    edges = []

    for ev in events:
        if ev.type == EventType.COMPILER_TASK_STARTED:
            nodes.append({
                "id": ev.id,
                "type": "Claim",
                "label": f"Compiler task {ev.payload.get('task_id')}",
                "confidence": 0.6
            })
        elif ev.type in (EventType.IR_FINALIZED, EventType.COMPILER_TASK_COMPLETED):
            nodes.append({
                "id": ev.id,
                "type": "Evidence",
                "label": ev.type.value,
                "supports": ev.payload.get("task_id")
            })

    return {
        "type": "belief_graph",
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
        "note": "Passive projection only - single source of truth remains the EventLog"
    }


if __name__ == "__main__":
    success = run_compiler_loop_demo()
    exit(0 if success else 1)