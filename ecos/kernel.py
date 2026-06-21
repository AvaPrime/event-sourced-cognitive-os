"""
E-COS Minimal MVP Cognitive Kernel (v0.3)

This is the executable runtime loop that proves the full architecture:

EventLog (truth) → Agent.match → SkillCompiler.compile → execute_plan (VM)
    → Event emission (including internal fork + MCP syscalls) → reduce → Projection

It is the smallest system that still demonstrates the complete claim:
- Deterministic event sourcing
- Skills as compiled execution graphs
- First-class internal branching inside skills
- MCP as stateless syscall boundary
- Pure projections

Everything else (distributed agents, skill IR, merging, versioning) is future expansion.

This file + the existing primitives + compiler = runnable E-COS MVP.
"""

from __future__ import annotations

from typing import List, Optional, Any

from .core.primitives import (
    Event, EventType, EventLog, Node, project, assert_deterministic_replay
)
from .skills.compiler import (
    compile_research_skill, execute_plan, RESEARCH_SKILL_SPEC
)


class StubMCPBridge:
    """
    Minimal stateless MCP Bridge for MVP.
    Pure syscall proxy — no state, no memory, deterministic mock results.
    In real system this would be the production MCP implementation.
    """
    def invoke(self, tool_name: str, args: dict) -> dict:
        # Deterministic mock (same input → same output)
        return {
            "tool": tool_name,
            "result": f"MOCK_RESULT::{tool_name.upper()}",
            "args_received": args,
            "note": "Resolved by StubMCPBridge (replace with real MCP in production)"
        }


class SimpleAgent:
    """
    Minimal Agent = Skill matcher + scheduler.
    In the full model this becomes the process scheduler for compiled graphs.
    For MVP: extremely simple pattern match on event content.
    """
    def match(self, event: Event, node: Node) -> List[str]:
        if event.type != EventType.USER_INPUT:
            return []

        content = event.payload.get("content", "").lower()
        if "research" in content:
            return ["ResearchSkill"]
        return []


class CognitiveKernel:
    """
    The single runtime loop of the minimal cognitive OS.

    while True:
        event = next_event()
        node = reduce(EventLog)
        for skill in Agent.match(...):
            plan = SkillCompiler.compile(...)
            execute_plan(...)   # emits events (fork, mcp_call, etc.)

    This class is the entire executable system in one place.
    """
    def __init__(self, session_id: Optional[str] = None):
        self.log = EventLog(session_id=session_id or "mvp_kernel_session")
        self.mcp = StubMCPBridge()
        self.agent = SimpleAgent()
        self.processed_count = 0

    def process_event(self, event: Event) -> List[Event]:
        """Process one event through the full kernel pipeline."""
        self.log.append(event)
        self.processed_count += 1

        current_branch = event.branch_id
        node = self.log.reduce_to_node(current_branch)

        matched_skills = self.agent.match(event, node)

        newly_emitted: List[Event] = []

        for skill_name in matched_skills:
            if skill_name == "ResearchSkill":
                # Compile the declarative spec into execution graph
                plan = compile_research_skill(node)

                # Execute the plan (VM) — this is where internal fork + MCP_CALL happen
                emitted = execute_plan(
                    plan,
                    self.log,
                    current_branch=current_branch,
                    mcp_bridge=self.mcp
                )
                newly_emitted.extend(emitted)

        return newly_emitted

    def run_mvp_demo(self, user_query: str = "Please research the impact of quantum computing on cryptography.") -> dict:
        """
        End-to-end MVP demonstration of the full kernel.

        Proves:
        - Event ingestion
        - Skill matching
        - Compilation of ResearchSkill
        - Execution with internal branching + MCP syscalls
        - State reduction
        - Determinism
        - Projections
        """
        print("=" * 70)
        print("E-COS MINIMAL MVP COGNITIVE KERNEL — END-TO-END DEMO")
        print("=" * 70)

        # 1. Ingest initial user event
        initial_event = Event(
            type=EventType.USER_INPUT,
            payload={"content": user_query},
            branch_id="main"
        )
        print(f"\n[1] Ingesting USER_INPUT event on 'main' branch...")
        self.process_event(initial_event)

        # 2. Show what happened after ResearchSkill compilation + execution
        node = self.log.reduce_to_node("main")
        print(f"\n[2] State after kernel processing:")
        print(f"    {node.summary()}")
        print(f"    Messages: {len(node.state.get('messages', []))}")
        print(f"    Tool calls emitted: {len([e for e in self.log.events if e.type == EventType.TOOL_CALL])}")
        print(f"    Branch forks emitted: {len([e for e in self.log.events if e.type == EventType.BRANCH_FORK])}")

        # 3. Demonstrate internal branching worked (new branches created by the skill)
        print(f"\n[3] Branches created by ResearchSkill internal fork:")
        branch_events = [e for e in self.log.events if e.type == EventType.BRANCH_FORK]
        for be in branch_events:
            print(f"    → {be.payload.get('new_branch')} (from step {be.payload.get('step_id')})")

        # 4. Determinism proof
        print(f"\n[4] Determinism verification (replay entire log):")
        is_deterministic = assert_deterministic_replay(self.log, "main")
        print(f"    {'PASS ✓' if is_deterministic else 'FAIL ✗'} — same events produce identical final node state")

        # 5. Projections (UI layer — pure functions over EventLog)
        print(f"\n[5] Projections (UI layer — pure functions over EventLog):")
        chat_view = project(self.log, view_type="chat", branch_id="main")
        timeline_view = project(self.log, view_type="timeline", branch_id="main")
        print(f"    Chat view: {len(chat_view.get('messages', []))} messages")
        print(f"    Timeline view: {len(timeline_view.get('events', []))} events")

        print("\n" + "=" * 70)
        print("MVP KERNEL DEMO COMPLETE")
        print("The full chain (Event → Match → Compile → Execute with fork/MCP → Reduce → Project) now runs.")
        print("=" * 70)

        return {
            "final_node": node.summary(),
            "events_processed": self.processed_count,
            "branches_created": len(branch_events),
            "deterministic": is_deterministic,
            "chat_messages": len(chat_view.get("messages", []))
        }


# ============================================================
# Convenience runner
# ============================================================

if __name__ == "__main__":
    kernel = CognitiveKernel(session_id="mvp_demo_001")
    result = kernel.run_mvp_demo()
    print(f"\nDemo result summary: {result}")