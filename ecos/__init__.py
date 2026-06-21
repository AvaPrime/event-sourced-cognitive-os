"""
E-COS: Event-Sourced Cognitive Operating System
A replayable, branching, deterministic computational substrate for cognition.

See core/primitives.py for the foundational model.
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

__version__ = "0.1.0"
__all__ = [
    "Event", "EventType", "Node", "Edge", "EventLog",
    "Skill", "MCPBridge", "Agent",
    "project", "assert_deterministic_replay",
]