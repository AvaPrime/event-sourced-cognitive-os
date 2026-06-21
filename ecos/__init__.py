"""
E-COS: Event-Sourced Cognitive Operating System
A replayable, branching, deterministic computational substrate for cognition.

v0.3.0-mvp: Minimal executable Cognitive Kernel (full runtime loop).
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

from .kernel import CognitiveKernel, SimpleAgent, StubMCPBridge

__version__ = "0.3.0-mvp"
__all__ = [
    "Event", "EventType", "Node", "Edge", "EventLog",
    "Skill", "MCPBridge", "Agent",
    "project", "assert_deterministic_replay",
    "compile_research_skill", "execute_plan", "RESEARCH_SKILL_SPEC", "Step",
    "CognitiveKernel", "SimpleAgent", "StubMCPBridge",
]