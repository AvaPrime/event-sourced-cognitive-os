"""
E-COS Skills Module v0.4

Skills are compiled execution graphs — first-class cognition programs
that run inside the Event Kernel VM.

This module now includes the full two-stage compiler pipeline:
    SkillSpec → SkillIR (assembly) → ExecutionPlan → Kernel VM
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
]