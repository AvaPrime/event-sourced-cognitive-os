"""
E-COS: Event-Sourced Cognitive Operating System
A replayable, branching, deterministic computational substrate for cognition.

v0.4.0-ir: Skill Intermediate Representation (two-stage compiler architecture).
"""

from .core.primitives import (
    Event,
    EventType,
    Node,
    Edge,
    EventLog,
    Skill,
    MCPBridge,
    Agent,
    project,
    assert_deterministic_replay,
)

from .skills.compiler import (
    compile_research_skill,
    execute_plan,
    RESEARCH_SKILL_SPEC,
    Step,
)

from .skills.ir import (
    IRNodeType,
    IRNode,
    SkillIR,
    compile_spec_to_ir,
    lower_ir_to_execution_plan,
    get_research_skill_ir,
)

from .kernel import CognitiveKernel, SimpleAgent, StubMCPBridge

__version__ = "0.4.0-ir"
__all__ = [
    "Event", "EventType", "Node", "Edge", "EventLog",
    "Skill", "MCPBridge", "Agent",
    "project", "assert_deterministic_replay",
    "compile_research_skill", "execute_plan", "RESEARCH_SKILL_SPEC", "Step",
    "IRNodeType", "IRNode", "SkillIR",
    "compile_spec_to_ir", "lower_ir_to_execution_plan", "get_research_skill_ir",
    "CognitiveKernel", "SimpleAgent", "StubMCPBridge",
]