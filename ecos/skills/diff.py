"""
E-COS Skill IR Diff Engine v0.5

Graph-aware semantic diff between two SkillIR versions.

Not text diff. Not JSON diff.
Structural, cognition-aware difference of reasoning programs.

Output model:
    IRDiff {
        added_nodes, removed_nodes, modified_nodes,
        added_edges, removed_edges,
        changed_state_contracts
    }

Enables:
- Cognitive version control
- Reasoning A/B testing
- Safe evolution + auditability of behavior drift
- Explainable changes (\"this fork was added because...\")

Identity rule: same entry + isomorphic graph structure + equivalent contracts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Set, Dict, Any, Tuple

from .ir import SkillIR, IRNode, IRNodeType


@dataclass
class IRDiff:
    """Structured difference between two SkillIRs."""
    ir_v1_name: str
    ir_v2_name: str
    added_nodes: List[str] = field(default_factory=list)
    removed_nodes: List[str] = field(default_factory=list)
    modified_nodes: List[str] = field(default_factory=list)  # payload or contract changed
    added_edges: List[Tuple[str, str]] = field(default_factory=list)
    removed_edges: List[Tuple[str, str]] = field(default_factory=list)
    changed_state_contracts: Dict[str, Any] = field(default_factory=dict)

    def is_empty(self) -> bool:
        return not any([
            self.added_nodes, self.removed_nodes, self.modified_nodes,
            self.added_edges, self.removed_edges, self.changed_state_contracts
        ])

    def summary(self) -> str:
        if self.is_empty():
            return "No structural differences (isomorphic)"
        return (f"IRDiff({self.ir_v1_name} → {self.ir_v2_name}): "
                f"+{len(self.added_nodes)} nodes, -{len(self.removed_nodes)} nodes, "
                f"+{len(self.added_edges)} edges, -{len(self.removed_edges)} edges")


def _node_signature(node: IRNode) -> str:
    """Stable signature for isomorphism / modification detection."""
    return f"{node.type.value}|{sorted(node.payload.items())}|{sorted(node.requires.items())}|{sorted(node.guarantees.items())}"


def diff_ir(ir1: SkillIR, ir2: SkillIR) -> IRDiff:
    """
    Compute structural semantic diff between two SkillIRs.

    Uses node signatures + edge sets for graph-aware comparison.
    Conservative but sufficient for v0.5 cognition diffing.
    """
    diff = IRDiff(ir_v1_name=ir1.name, ir_v2_name=ir2.name)

    # Node sets by signature
    sig1 = {_node_signature(n): n.id for n in ir1.nodes}
    sig2 = {_node_signature(n): n.id for n in ir2.nodes}

    # Added / removed by signature
    added_sigs = set(sig2.keys()) - set(sig1.keys())
    removed_sigs = set(sig1.keys()) - set(sig2.keys())

    for s in added_sigs:
        diff.added_nodes.append(sig2[s])
    for s in removed_sigs:
        diff.removed_nodes.append(sig1[s])

    # Modified nodes (same id but different signature — rare in clean IRs, but possible)
    common_ids = set(n.id for n in ir1.nodes) & set(n.id for n in ir2.nodes)
    for nid in common_ids:
        n1 = ir1.get_node(nid)
        n2 = ir2.get_node(nid)
        if n1 and n2 and _node_signature(n1) != _node_signature(n2):
            diff.modified_nodes.append(nid)

    # Edge diff (simple set difference)
    edges1 = set(ir1.edges)
    edges2 = set(ir2.edges)
    diff.added_edges = list(edges2 - edges1)
    diff.removed_edges = list(edges1 - edges2)

    # State contract changes
    if ir1.state_contract != ir2.state_contract:
        diff.changed_state_contracts = {
            "v1": ir1.state_contract,
            "v2": ir2.state_contract
        }

    return diff


def are_isomorphic(ir1: SkillIR, ir2: SkillIR) -> bool:
    """Quick structural isomorphism check (entry + contract keys + node/edge count)."""
    if ir1.entry_id != ir2.entry_id:
        return False
    if ir1.state_contract.keys() != ir2.state_contract.keys():
        return False
    if len(ir1.nodes) != len(ir2.nodes) or len(ir1.edges) != len(ir2.edges):
        return False
    return True


if __name__ == "__main__":
    from .ir import get_research_skill_ir
    from .optimizer import optimize_ir

    print("E-COS IR Diff Engine v0.5 — Self-test")
    print("=" * 60)

    ir_v1 = get_research_skill_ir()
    ir_v2 = optimize_ir(ir_v1)  # simulate an evolved version

    d = diff_ir(ir_v1, ir_v2)
    print(f"Diff result: {d.summary()}")
    print(f"Isomorphic (quick check): {are_isomorphic(ir_v1, ir_v2)}")

    if not d.is_empty():
        print(f"Added nodes: {d.added_nodes}")
        print(f"Removed nodes: {d.removed_nodes}")

    print("\nDiff engine ready. Cognition programs are now version-diffable.")