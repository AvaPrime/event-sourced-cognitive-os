"""
E-COS: Event-Sourced Cognitive Operating System
A replayable, branching, deterministic computational substrate for cognition.

v0.2.0-dev: Skills are now compiled execution graphs (Option C foundation).
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

__version__ = "0.2.0-dev"
__all__ = [
    "Event", "EventType", "Node", "Edge", "EventLog",
    "Skill", "MCPBridge", "Agent",
    "project", "assert_deterministic_replay",
    "compile_research_skill", "execute_plan", "RESEARCH_SKILL_SPEC", "Step",
]