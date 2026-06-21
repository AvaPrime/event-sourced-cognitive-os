"""
E-COS: Event-Sourced Cognitive Operating System
A replayable, branching, deterministic computational substrate for cognition.

v0.5.0-optimizer: IR Optimizer + Skill Diff Engine (self-optimizing cognition compiler).
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

from .skills.optimizer import (
    optimize_ir,
    dead_node_elimination,
    mcp_call_deduplication,
    fork_flattening,
    merge_hoisting,
    semantic_equivalence,
)

from .skills.diff import (
    IRDiff,
    diff_ir,
    are_isomorphic,
)

from .kernel import CognitiveKernel, SimpleAgent, StubMCPBridge

__version__ = "0.5.0-optimizer"
__all__ = [
    "Event", "EventType", "Node", "Edge", "EventLog",
    "Skill", "MCPBridge", "Agent",
    "project", "assert_deterministic_replay",
    "compile_research_skill", "execute_plan", "RESEARCH_SKILL_SPEC", "Step",
    "IRNodeType", "IRNode", "SkillIR",
    "compile_spec_to_ir", "lower_ir_to_execution_plan", "get_research_skill_ir",
    "optimize_ir", "dead_node_elimination", "mcp_call_deduplication",
    "fork_flattening", "merge_hoisting", "semantic_equivalence",
    "IRDiff", "diff_ir", "are_isomorphic",
    "CognitiveKernel", "SimpleAgent", "StubMCPBridge",
]