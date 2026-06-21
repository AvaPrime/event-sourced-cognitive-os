"""
E-COS Skills Module v0.5

Skills are compiled execution graphs — first-class cognition programs
that run inside the Event Kernel VM.

Full pipeline now includes:
    SkillSpec → SkillIR → [Optimizer Passes] → OptimizedIR → Lowering → ExecutionPlan → Kernel
    + parallel Diff Engine for versioned cognition.
"""

from .compiler import (
    compile_research_skill,
    execute_plan,
    RESEARCH_SKILL_SPEC,
    Step,
)

from .ir import (
    IRNodeType,
    IRNode,
    SkillIR,
    compile_spec_to_ir,
    lower_ir_to_execution_plan,
    get_research_skill_ir,
)

from .optimizer import (
    optimize_ir,
    dead_node_elimination,
    mcp_call_deduplication,
    fork_flattening,
    merge_hoisting,
    semantic_equivalence,
)

from .diff import (
    IRDiff,
    diff_ir,
    are_isomorphic,
)

__all__ = [
    "compile_research_skill",
    "execute_plan",
    "RESEARCH_SKILL_SPEC",
    "Step",
    "IRNodeType",
    "IRNode",
    "SkillIR",
    "compile_spec_to_ir",
    "lower_ir_to_execution_plan",
    "get_research_skill_ir",
    "optimize_ir",
    "dead_node_elimination",
    "mcp_call_deduplication",
    "fork_flattening",
    "merge_hoisting",
    "semantic_equivalence",
    "IRDiff",
    "diff_ir",
    "are_isomorphic",
]