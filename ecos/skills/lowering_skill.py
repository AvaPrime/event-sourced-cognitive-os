"""
LoweringSkill — Minimal deterministic compiler-domain skill for E-COS v0.1

Emits a deterministic sequence of events representing AST lowering.
Now satisfies the minimal EventContract requirements and attaches intent.
"""

from __future__ import annotations

from typing import List, Dict, Any

from ..core.primitives import Event, EventType, Node


class LoweringSkill:
    """
    Deterministic Skill.
    All emitted events now carry required payload keys + intent for explainability.
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
        task_id = triggering_event.payload.get("task_id", "unknown")
        source = triggering_event.payload.get("source", "")

        emitted: List[Event] = []

        # IR root
        emitted.append(Event(
            type=EventType.IR_NODE_CREATED,
            payload={
                "task_id": task_id,
                "node_type": "Module",
                "name": "root"
            },
            causality_id=triggering_event.id,
            branch_id=triggering_event.branch_id,
            intent="create_ir_root_node"
        ))

        # Lowering steps with intent
        steps = ["parse", "resolve", "lower_to_ir"]
        for i, step in enumerate(steps):
            emitted.append(Event(
                type=EventType.LOWERING_STEP,
                payload={
                    "task_id": task_id,
                    "step": step,
                    "step_index": i
                },
                causality_id=triggering_event.id,
                branch_id=triggering_event.branch_id,
                intent=f"lowering_step_{step}"
            ))

        # Finalize
        emitted.append(Event(
            type=EventType.IR_FINALIZED,
            payload={
                "task_id": task_id,
                "final_node_count": 1 + len(steps)
            },
            causality_id=triggering_event.id,
            branch_id=triggering_event.branch_id,
            intent="finalize_ir"
        ))

        # Task complete
        emitted.append(Event(
            type=EventType.COMPILER_TASK_COMPLETED,
            payload={
                "task_id": task_id,
                "result": "lowering_complete"
            },
            causality_id=triggering_event.id,
            branch_id=triggering_event.branch_id,
            intent="complete_compiler_task"
        ))

        return emitted
