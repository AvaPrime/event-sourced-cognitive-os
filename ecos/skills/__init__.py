"""
E-COS Skills Module v0.1

Skills are compiled execution graphs — first-class cognition programs
that run inside the Event Kernel VM.

This module provides the Skill Compiler and execution primitives.
"""

from .compiler import (
    compile_research_skill,
    execute_plan,
    RESEARCH_SKILL_SPEC,
    Step,
)

__all__ = [
    "compile_research_skill",
    "execute_plan",
    "RESEARCH_SKILL_SPEC",
    "Step",
]