"""
E-COS Skill Intermediate Representation (IR) v0.4

This is the typed, deterministic, graph-based \"assembly language\" of cognition.

Position in pipeline:
    SkillSpec (declarative, human/LLM-authored)
         ↓
    SkillIR (static, analyzable, versionable, diffable)
         ↓
    ExecutionPlan / Step list (runtime, lowered for kernel VM)
         ↓
    Kernel loop (event emission)

IR enables:
- Deterministic traceability (Spec → IR → Events)
- Skill versioning + safe evolution
- Structural diffing of reasoning strategies
- Future optimization passes (common subexpression elimination, fork collapsing, etc.)
- Debuggable cognition (\"show me the exact IR node where this branch diverged\")
- Pre-execution validation via per-node state contracts

IR is NEVER executed directly. It is lowered into the ephemeral ExecutionPlan
that the CognitiveKernel VM consumes.

This completes the two-stage compiler architecture for structured cognition:
SkillSpec = source
SkillIR   = assembly
ExecutionPlan = bytecode
Kernel    = CPU
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..core.primitives import Node


class IRNodeType(str, Enum):
    """The 7 canonical IR node types for cognition graphs."""
    ENTRY = "ENTRY"
    OPERATION = "OPERATION"      # pure internal reasoning step
    MCP_CALL = "MCP_CALL"        # explicit syscall boundary
    FORK = "FORK"                # first-class cognitive branching
    MERGE = "MERGE"              # reconciliation of branches
    EMIT = "EMIT"                # produce final/output event
    EXIT = "EXIT"                # terminal node


@dataclass
class IRNode:
    """A single node in the Skill Intermediate Representation graph."""
    id: str
    type: IRNodeType
    payload: Dict[str, Any] = field(default_factory=dict)
    # State contract attached directly to the node (critical for safety)
    requires: Dict[str, Any] = field(default_factory=dict)   # e.g. {"query": "non_null"}
    guarantees: Dict[str, Any] = field(default_factory=dict) # e.g. {"facts": "non_empty_list"}

    def __repr__(self) -> str:
        return f"IRNode({self.id}, {self.type.value})"


@dataclass
class SkillIR:
    """
    A complete, static, deterministic intermediate representation of a Skill.

    This is the canonical form that enables versioning, diffing, and optimization.
    """
    name: str
    version: str
    nodes: List[IRNode]
    edges: List[Tuple[str, str]]          # (from_node_id, to_node_id)
    entry_id: str
    exit_id: str
    state_contract: Dict[str, Any] = field(default_factory=dict)

    def get_node(self, node_id: str) -> Optional[IRNode]:
        for n in self.nodes:
            if n.id == node_id:
                return n
        return None

    def topological_order(self) -> List[IRNode]:
        """Simple topological sort (sufficient for DAGs in v0.4)."""
        # For MVP we assume the compiler emits nodes in roughly topological order
        return self.nodes

    def __repr__(self) -> str:
        return f"SkillIR({self.name} v{self.version}, {len(self.nodes)} nodes, {len(self.edges)} edges)"


# ============================================================
# IR Compiler (Spec → IR) — pure and deterministic
# ============================================================

def compile_spec_to_ir(spec: Dict[str, Any], current_node: Node) -> SkillIR:
    """
    Pure compilation from declarative SkillSpec to SkillIR.

    For v0.4 we implement the canonical ResearchSkill as a rich IR graph
    that demonstrates FORK → parallel MCP_CALL paths → MERGE.
    """
    if spec.get("name") != "ResearchSkill":
        raise NotImplementedError("v0.4 IR compiler supports only ResearchSkill")

    nodes: List[IRNode] = []
    edges: List[Tuple[str, str]] = []

    # ENTRY
    entry = IRNode(
        id="entry",
        type=IRNodeType.ENTRY,
        payload={"skill": spec["name"]},
        requires={"messages": "present"}
    )
    nodes.append(entry)

    # OPERATION: decompose_query
    decompose = IRNode(
        id="decompose_query",
        type=IRNodeType.OPERATION,
        payload={"operation": "decompose_query"},
        requires={"query": "non_null"},
        guarantees={"sub_queries": "list"}
    )
    nodes.append(decompose)
    edges.append(("entry", "decompose_query"))

    # FORK (core cognitive branching primitive)
    fork_node = IRNode(
        id="fork_branches",
        type=IRNodeType.FORK,
        payload={
            "branches": ["factual_retrieval", "reasoning_synthesis"],
            "strategy": "parallel_hypothesis_exploration"
        }
    )
    nodes.append(fork_node)
    edges.append(("decompose_query", "fork_branches"))

    # Branch A: factual retrieval path
    retrieve_facts = IRNode(
        id="retrieve_facts",
        type=IRNodeType.MCP_CALL,
        payload={"tool": "web_search", "query_field": "sub_queries"},
        requires={"sub_queries": "non_empty"},
        guarantees={"facts": "list_of_sources"}
    )
    nodes.append(retrieve_facts)
    edges.append(("fork_branches", "retrieve_facts"))

    # Branch B: reasoning synthesis path
    retrieve_reasoning = IRNode(
        id="retrieve_reasoning_paths",
        type=IRNodeType.MCP_CALL,
        payload={"tool": "llm_reasoning", "context_field": "sub_queries"},
        requires={"sub_queries": "non_empty"},
        guarantees={"reasoning_paths": "list"}
    )
    nodes.append(retrieve_reasoning)
    edges.append(("fork_branches", "retrieve_reasoning_paths"))

    # MERGE (reconciliation point)
    merge = IRNode(
        id="merge_results",
        type=IRNodeType.MERGE,
        payload={"strategy": "synthesis_parallel_branches"},
        requires={"facts": "present", "reasoning_paths": "present"},
        guarantees={"synthesis": "unified_answer"}
    )
    nodes.append(merge)
    edges.append(("retrieve_facts", "merge_results"))
    edges.append(("retrieve_reasoning_paths", "merge_results"))

    # OPERATION: synthesize
    synthesize = IRNode(
        id="synthesize",
        type=IRNodeType.OPERATION,
        payload={"operation": "final_synthesis"},
        requires={"synthesis": "present"},
        guarantees={"final_answer": "string"}
    )
    nodes.append(synthesize)
    edges.append(("merge_results", "synthesize"))

    # EMIT
    emit = IRNode(
        id="emit_final",
        type=IRNodeType.EMIT,
        payload={"event_type": "SYNTHESIS_COMPLETE", "payload_fields": ["final_answer"]}
    )
    nodes.append(emit)
    edges.append(("synthesize", "emit_final"))

    # EXIT
    exit_node = IRNode(
        id="exit",
        type=IRNodeType.EXIT,
        payload={"skill": spec["name"]}
    )
    nodes.append(exit_node)
    edges.append(("emit_final", "exit"))

    ir = SkillIR(
        name=spec["name"],
        version=spec.get("version", "0.4"),
        nodes=nodes,
        edges=edges,
        entry_id="entry",
        exit_id="exit",
        state_contract=spec.get("state_contract", {})
    )
    return ir


def lower_ir_to_execution_plan(ir: SkillIR) -> List[Dict[str, Any]]:
    """
    Lower SkillIR (static graph) into the runtime ExecutionPlan format
    expected by the existing execute_plan VM.

    This is a deterministic lowering pass. In future versions this can
    include optimization rewrites before lowering.
    """
    plan: List[Dict[str, Any]] = []

    for node in ir.topological_order():
        if node.type == IRNodeType.ENTRY:
            continue  # implicit
        if node.type == IRNodeType.EXIT:
            continue

        step = {
            "id": node.id,
            "name": node.payload.get("operation") or node.payload.get("tool") or node.type.value,
            "type": {
                IRNodeType.OPERATION: "internal",
                IRNodeType.MCP_CALL: "mcp_call",
                IRNodeType.FORK: "fork",
                IRNodeType.MERGE: "internal",   # merge is handled implicitly in current VM
                IRNodeType.EMIT: "emit_final",
            }.get(node.type, "internal"),
            "payload": {
                "ir_node_id": node.id,
                "ir_type": node.type.value,
                **node.payload
            },
            "config": node.payload,
            "requires": node.requires,
            "guarantees": node.guarantees,
        }

        if node.type == IRNodeType.FORK:
            step["branches"] = node.payload.get("branches", ["branch_a", "branch_b"])

        plan.append(step)

    return plan


# ============================================================
# Convenience: ResearchSkill IR (for inspection / debugging)
# ============================================================

def get_research_skill_ir(current_node: Optional[Node] = None) -> SkillIR:
    """Return the canonical ResearchSkill as a fully expanded SkillIR for inspection."""
    dummy_node = current_node or Node(state={"messages": [{"role": "user", "content": "research example"}]})
    return compile_spec_to_ir(
        {"name": "ResearchSkill", "version": "0.4"},
        dummy_node
    )


# ============================================================
# Demo / introspection
# ============================================================

if __name__ == "__main__":
    print("E-COS Skill IR v0.4 — Self-test & ResearchSkill Visualization")
    print("=" * 72)

    ir = get_research_skill_ir()

    print(f"\n[1] Compiled ResearchSkill to SkillIR:")
    print(f"    {ir}")
    print(f"    Nodes: {len(ir.nodes)}")
    print(f"    Edges: {len(ir.edges)}")

    print("\n[2] IR Graph (textual representation):")
    for node in ir.nodes:
        print(f"    {node.id:25} [{node.type.value:12}]  requires={node.requires} guarantees={node.guarantees}")

    print("\n[3] Lowering IR → ExecutionPlan (for kernel VM):")
    plan = lower_ir_to_execution_plan(ir)
    for step in plan:
        print(f"    {step['id']:25} → type={step['type']:12}  ir_node={step['payload'].get('ir_node_id')}")

    print("\n[4] Key structural properties now available:")
    print("    • Deterministic Spec → IR → Plan traceability")
    print("    • Per-node state contracts for pre-validation")
    print("    • FORK / MERGE as first-class structural IR constructs")
    print("    • MCP_CALL nodes explicitly visible (no hidden logic)")
    print("    • Ready for diffing, versioning, and future optimizer passes")

    print("\n" + "=" * 72)
    print("Skill IR layer complete. Cognition now has a stable assembly representation.")