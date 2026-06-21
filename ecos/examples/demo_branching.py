#!/usr/bin/env python3
"""
E-COS Demo: Branching Cognition + Deterministic Replay

This demonstrates:
- Event sourcing as the single source of truth
- Node reduction from event history
- Git-style branching of execution / conversation
- Different skills/paths producing divergent states
- Pure projections (chat view)
- Determinism check
"""

from datetime import datetime, timezone
import sys
from pathlib import Path

# Make runnable from repo root: PYTHONPATH=. python -m ecos.examples.demo_branching
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ecos.core.primitives import (
    Event, EventType, EventLog, project, assert_deterministic_replay
)


def main():
    print("=" * 70)
    print("E-COS v0.1 — Event-Sourced Cognitive Operating System Demo")
    print("=" * 70)

    # 1. Create the event log (the truth)
    log = EventLog(session_id="demo_session_001")
    print(f"\n[1] Created {log}")

    # 2. Root branch events (main conversation)
    print("\n[2] Seeding 'main' branch with initial events...")

    log.append(Event(
        type=EventType.USER_INPUT,
        payload={"content": "Research the impact of quantum computing on cryptography."},
        branch_id="main"
    ))

    log.append(Event(
        type=EventType.AGENT_DECISION,
        payload={
            "reasoning": "I need to break this into sub-questions and use research tools.",
            "chosen_skills": ["query_decomposition", "literature_search"]
        },
        branch_id="main",
        causality_id=log.events[-1].id
    ))

    log.append(Event(
        type=EventType.SKILL_RESULT,
        payload={"skill_name": "query_decomposition", "output": ["Shor's algorithm", "post-quantum crypto standards"]},
        branch_id="main"
    ))

    print(f"   Events in main: {len(log.get_events('main'))}")

    # 3. Reduce to current state (Node)
    node_main = log.reduce_to_node("main")
    print(f"\n[3] Reduced Node for 'main': {node_main.summary()}")
    print(f"    State keys: {list(node_main.state.keys())}")
    print(f"    Messages so far: {len(node_main.state.get('messages', []))}")

    # 4. Fork into two competing research strategies (the key leap)
    print("\n[4] Forking cognition into two parallel branches (Strategy A vs B)...")

    branch_a = log.fork_branch(
        parent_branch="main",
        new_branch_id="research_strategy_A",
        fork_event_payload={"strategy": "Focus on Shor's algorithm impact + timeline"}
    )

    branch_b = log.fork_branch(
        parent_branch="main",
        new_branch_id="research_strategy_B",
        fork_event_payload={"strategy": "Focus on NIST post-quantum migration paths"}
    )

    print(f"   Created branches: {branch_a}, {branch_b}")

    # 5. Divergent evolution on each branch
    print("\n[5] Evolving branches independently...")

    # Branch A: aggressive technical deep-dive
    log.append(Event(
        type=EventType.USER_INPUT,
        payload={"content": "Deep dive on Shor's algorithm breaking RSA-2048 timelines."},
        branch_id=branch_a
    ))
    log.append(Event(
        type=EventType.SKILL_RESULT,
        payload={"skill_name": "literature_search", "papers": 12, "key_finding": "Estimates vary 5-15 years for cryptographically relevant quantum computer."},
        branch_id=branch_a
    ))
    log.append(Event(
        type=EventType.STATE_TRANSITION,
        payload={"state_patch": {"research_focus": "technical_risk", "urgency": "high"}},
        branch_id=branch_a
    ))

    # Branch B: policy + migration focused
    log.append(Event(
        type=EventType.USER_INPUT,
        payload={"content": "What are the current NIST recommendations and enterprise migration costs?"},
        branch_id=branch_b
    ))
    log.append(Event(
        type=EventType.SKILL_RESULT,
        payload={"skill_name": "policy_retrieval", "standards": ["ML-KEM", "ML-DSA"], "migration_notes": "Hybrid schemes recommended now."},
        branch_id=branch_b
    ))
    log.append(Event(
        type=EventType.STATE_TRANSITION,
        payload={"state_patch": {"research_focus": "migration_strategy", "urgency": "medium"}},
        branch_id=branch_b
    ))

    # 6. Show divergent states
    print("\n[6] Divergent states after independent evolution:")
    node_a = log.reduce_to_node(branch_a)
    node_b = log.reduce_to_node(branch_b)

    print(f"\n   Branch A ({branch_a}):")
    print(f"     Focus: {node_a.state.get('research_focus')}")
    print(f"     Urgency: {node_a.state.get('urgency')}")
    print(f"     Messages: {len(node_a.state.get('messages', []))}")

    print(f"\n   Branch B ({branch_b}):")
    print(f"     Focus: {node_b.state.get('research_focus')}")
    print(f"     Urgency: {node_b.state.get('urgency')}")
    print(f"     Messages: {len(node_b.state.get('messages', []))}")

    # 7. Pure UI projections (no logic in UI)
    print("\n[7] Projecting different views (UI as pure function over graph):")
    chat_view_a = project(log, view_type="chat", branch_id=branch_a)
    timeline_view = project(log, view_type="timeline", branch_id="main")

    print(f"   Chat view on A: {len(chat_view_a['messages'])} messages")
    print(f"   Timeline events on main: {len(timeline_view['events'])}")

    # 8. Determinism verification (critical property)
    print("\n[8] Verifying deterministic replay (same events → identical state):")
    is_deterministic = assert_deterministic_replay(log, branch_a)
    print(f"   Determinism check on branch A: {'PASS ✓' if is_deterministic else 'FAIL ✗'}")

    # 9. Time travel / audit example
    print("\n[9] Time-travel: state at different points in history")
    early_events = log.get_events(branch_a)
    if len(early_events) > 2:
        mid_point = early_events[2].timestamp
        node_early = log.reduce_to_node(branch_a, up_to=mid_point)
        print(f"   Early state on A (after {len(node_early.event_ids)} events): {node_early.state.get('research_focus', 'N/A')}")

    print("\n" + "=" * 70)
    print("Demo complete. The event graph is the OS.")
    print("Branches are independent computations sharing causal history.")
    print("Everything is replayable, auditable, and forkable.")
    print("=" * 70)


if __name__ == "__main__":
    main()