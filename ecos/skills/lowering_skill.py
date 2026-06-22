"""
LoweringSkill — Minimal deterministic compiler-domain skill for E-COS v0.1

This skill does NOT perform heavy compilation.
It emits a deterministic sequence of events that *represent* the lowering process.

This proves that real domain work (Codessa-style compiler construction)
can be expressed purely as event emission inside the E-COS kernel.
"""

from __future__ import annotations

from typing import List, Dict, Any

from ..core.primitives import Event, EventType, Node


class LoweringSkill:
    """
    Deterministic Skill that turns a COMPILER_TASK_STARTED into
    a sequence of IR construction events.

    Constraint: same input Node + Event → identical emitted events.
    """
    name = "LoweringSkill"
    description = "Emits deterministic IR lowering event trace for compiler tasks"
    version = "0.1"

    def matches(self, event: Event, node: Node) -> bool:
        return event.type == EventType.COMPILER_TASK_STARTED

    def execute(
        self,
        current_node: Node,
        triggering_event: Event,
        context: Dict[str, Any]
    ) -> List[Event]:
        """
        Pure emission of lowering events.
        In later versions this will call into Codessa's stricter reducer.
        """
        task_id = triggering_event.payload.get("task_id", "unknown")
        source = triggering_event.payload.get("source", "")

        emitted: List[Event] = []

        # 1. Announce IR root node creation
        emitted.append(Event(
            type=EventType.IR_NODE_CREATED,
            payload={
                "task_id": task_id,
                "node_type": "Module",
                "name": "root",
                "source_ref": source[:64] if source else None
            },
            causality_id=triggering_event.id,
            branch_id=triggering_event.branch_id
        ))

        # 2. Emit a few deterministic lowering steps (simulating passes)
        steps = ["parse", "resolve", "lower_to_ir"]
        for i, step in enumerate(steps):
            emitted.append(Event(
                type=EventType.LOWERING_STEP,
                payload={
                    "task_id": task_id,
                    "step": step,
                    "step_index": i,
                    "deterministic": True
                },
                causality_id=triggering_event.id,
                branch_id=triggering_event.branch_id
            ))

        # 3. Finalize
        emitted.append(Event(
            type=EventType.IR_FINALIZED,
            payload={
                "task_id": task_id,
                "final_node_count": 1 + len(steps),
                "status": "ok"
            },
            causality_id=triggering_event.id,
            branch_id=triggering_event.branch_id
        ))

        # 4. Task complete
        emitted.append(Event(
            type=EventType.COMPILER_TASK_COMPLETED,
            payload={
                "task_id": task_id,
                "result": "lowering_complete",
                "events_emitted": len(emitted)
            },
            causality_id=triggering_event.id,
            branch_id=triggering_event.branch_id
        ))

        return emitted
