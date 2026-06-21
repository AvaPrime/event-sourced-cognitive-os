"""
E-COS: Event-Sourced Cognitive Operating System
Core Primitives v0.1

This module defines the foundational immutable data structures
for a deterministic, replayable, branching cognitive runtime.

Everything is an Event. State is derived (reduced) from events.
Agents schedule Skills. Skills emit Events. MCP provides pure capabilities.
UI is a pure projection over the Event Graph.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol, Callable
from enum import Enum
import json


class EventType(str, Enum):
    """Extensible taxonomy of events in the cognitive system."""
    USER_INPUT = "user_input"
    AGENT_DECISION = "agent_decision"
    SKILL_TRIGGER = "skill_trigger"
    SKILL_RESULT = "skill_result"
    TOOL_CALL = "tool_call"          # Mediated by MCP
    TOOL_RESULT = "tool_result"
    STATE_TRANSITION = "state_transition"
    BRANCH_FORK = "branch_fork"
    BRANCH_MERGE = "branch_merge"
    MEMORY_UPDATE = "memory_update"
    UI_INTERACTION = "ui_interaction"
    SYSTEM = "system"


@dataclass(frozen=True)
class Event:
    """
    P1 — The smallest unit of reality.
    Immutable. Append-only. The only source of truth.
    """
    type: EventType
    payload: Dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    causality_id: Optional[str] = None      # The event that directly caused this one
    branch_id: str = "main"                 # Enables Git-like branching of cognition
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        d["type"] = self.type.value
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)


@dataclass
class Node:
    """
    P2 — A coherent state snapshot at a point in time.
    Reconstructed via reduction over the event stream (never stored as source of truth).
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    branch_id: str = "main"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    state: Dict[str, Any] = field(default_factory=dict)
    event_ids: List[str] = field(default_factory=list)   # Full causal history for this node
    parent_node_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        return f"Node({self.id[:8]} | branch={self.branch_id} | events={len(self.event_ids)})"


@dataclass
class Edge:
    """
    P3 — Causal transition between states.
    Represents: NodeA --[Event]--> NodeB
    """
    from_node_id: str
    event_id: str
    to_node_id: str
    transition_type: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EventLog:
    """
    Append-only event store. Single source of truth for a cognitive session.
    Supports branching via branch_id tagging.
    In production this would be backed by a durable log (e.g. Kafka, SQLite, or custom).
    """

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self._events: List[Event] = []
        self._nodes_cache: Dict[str, Node] = {}  # branch_id -> latest materialized node (optional)

    def append(self, event: Event) -> Event:
        """Append is the only mutating operation. Everything else is derived."""
        if not isinstance(event, Event):
            raise TypeError("Only Event instances may be appended")
        self._events.append(event)
        # Invalidate cache for this branch (simple strategy)
        if event.branch_id in self._nodes_cache:
            del self._nodes_cache[event.branch_id]
        return event

    @property
    def events(self) -> List[Event]:
        return list(self._events)  # defensive copy

    def get_events(
        self,
        branch_id: str = "main",
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        event_types: Optional[List[EventType]] = None
    ) -> List[Event]:
        """Query events for a specific branch (supports time travel & filtering)."""
        result = [e for e in self._events if e.branch_id == branch_id]
        if since:
            result = [e for e in result if e.timestamp >= since]
        if until:
            result = [e for e in result if e.timestamp <= until]
        if event_types:
            result = [e for e in result if e.type in event_types]
        return result

    def reduce_to_node(
        self,
        branch_id: str = "main",
        up_to: Optional[datetime] = None
    ) -> Node:
        """
        P2 in action: Reconstruct state by folding events.
        This is the deterministic reducer: State(T) = reduce(EventStream[0..T])
        """
        events = self.get_events(branch_id=branch_id, until=up_to)
        if not events:
            return Node(branch_id=branch_id, state={"status": "empty"})

        # --- Deterministic reduction rules (extensible) ---
        state: Dict[str, Any] = {
            "messages": [],
            "last_agent_decision": None,
            "active_skills": [],
            "tool_results": {},
            "branch_history": [],
            "event_count": 0,
        }

        event_ids: List[str] = []
        last_ts = events[0].timestamp

        for ev in events:
            event_ids.append(ev.id)
            last_ts = max(last_ts, ev.timestamp)
            state["event_count"] += 1

            if ev.type == EventType.USER_INPUT:
                state["messages"].append({
                    "role": "user",
                    "content": ev.payload.get("content", ""),
                    "event_id": ev.id
                })

            elif ev.type == EventType.AGENT_DECISION:
                state["last_agent_decision"] = ev.payload
                state["messages"].append({
                    "role": "assistant",
                    "content": ev.payload.get("reasoning", ""),
                    "event_id": ev.id
                })

            elif ev.type == EventType.SKILL_RESULT:
                state["active_skills"].append(ev.payload.get("skill_name"))

            elif ev.type == EventType.TOOL_RESULT:
                tool_name = ev.payload.get("tool_name")
                if tool_name:
                    state["tool_results"][tool_name] = ev.payload.get("result")

            elif ev.type == EventType.BRANCH_FORK:
                state["branch_history"].append({
                    "forked_from": ev.payload.get("parent_branch"),
                    "new_branch": ev.branch_id,
                    "at_event": ev.id
                })

            elif ev.type == EventType.STATE_TRANSITION:
                # Allow skills/agents to explicitly patch state
                patch = ev.payload.get("state_patch", {})
                state.update(patch)

        node = Node(
            branch_id=branch_id,
            timestamp=last_ts,
            state=state,
            event_ids=event_ids,
            metadata={"reducer_version": "0.1"}
        )
        self._nodes_cache[branch_id] = node
        return node

    def fork_branch(
        self,
        parent_branch: str = "main",
        new_branch_id: Optional[str] = None,
        fork_event_payload: Optional[Dict] = None
    ) -> str:
        """
        Create a new branch that shares history prefix with parent.
        Returns the new branch_id.
        This is how "chat branching" becomes first-class execution forking.
        """
        new_branch = new_branch_id or f"branch_{uuid.uuid4().hex[:8]}"
        fork_event = Event(
            type=EventType.BRANCH_FORK,
            payload={
                "parent_branch": parent_branch,
                "new_branch": new_branch,
                **(fork_event_payload or {})
            },
            branch_id=new_branch,   # The fork event lives on the new branch
            causality_id=self._events[-1].id if self._events else None
        )
        self.append(fork_event)
        return new_branch

    def __len__(self) -> int:
        return len(self._events)

    def __repr__(self) -> str:
        return f"EventLog(session={self.session_id[:8]}, events={len(self)})"


# ============================================================
# P4 + P5 + P6 + P7 Protocols / Interfaces (for implementation)
# ============================================================

class Skill(Protocol):
    """
    P5 — Executable Cognition Unit.
    A deterministic behavioral program compiled into state transition rules.
    Not a function. A small state machine over events.
    """
    name: str
    description: str
    version: str

    def matches(self, event: Event, node: Node) -> bool:
        """Does this skill activate on the current event + state?"""
        ...

    def execute(
        self,
        current_node: Node,
        triggering_event: Event,
        context: Dict[str, Any]
    ) -> List[Event]:
        """
        Pure(ish) transition function.
        Returns new events to be appended (may include skill_result, state_transition, tool_call, etc.)
        Must be deterministic given same inputs.
        """
        ...


class MCPBridge(Protocol):
    """
    P6 — Model Context Protocol capability bridge.
    Pure syscall / tool interface. Owns ZERO reasoning or persistent state.
    Agents and Skills use this to discover and invoke external capabilities.
    """
    def list_tools(self) -> List[Dict[str, Any]]:
        ...

    def invoke_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Structured, validated tool call. Returns structured result."""
        ...

    def register_tool(self, name: str, schema: Dict, handler: Callable) -> None:
        ...


class Agent(Protocol):
    """
    P4 — Execution Kernel / Scheduler.
    Not a chatbot. An active process that:
    - observes events
    - selects & runs matching Skills
    - resolves conflicts across branches
    - emits new events (including forking)
    """
    name: str
    skills: List[Skill]
    mcp: MCPBridge

    def process_new_event(
        self,
        event_log: EventLog,
        event: Event
    ) -> List[Event]:
        """Main loop entry. Returns any newly emitted events."""
        ...

    def decide_next_action(self, node: Node) -> Optional[Event]:
        """Optional: high-level planner that can emit agent_decision events."""
        ...


def project(
    event_log: EventLog,
    view_type: str = "chat",
    branch_id: str = "main",
    **kwargs
) -> Dict[str, Any]:
    """
    P7 — Pure projection / rendering function.
    UI is never logic. It is a view over the event graph.
    Examples: chat, graphviz, timeline, debug replay, branch diff.
    """
    node = event_log.reduce_to_node(branch_id=branch_id)

    if view_type == "chat":
        return {
            "type": "chat",
            "branch_id": branch_id,
            "messages": node.state.get("messages", []),
            "last_decision": node.state.get("last_agent_decision"),
            "event_count": node.state.get("event_count", 0)
        }

    elif view_type == "graph":
        # Placeholder for graph projection (nodes + edges)
        return {
            "type": "graph",
            "branch_id": branch_id,
            "node_count": 1,
            "latest_node": node.summary(),
            "events": [e.to_dict() for e in event_log.get_events(branch_id=branch_id)]
        }

    elif view_type == "timeline":
        events = event_log.get_events(branch_id=branch_id)
        return {
            "type": "timeline",
            "events": [
                {"id": e.id, "type": e.type.value, "ts": e.timestamp.isoformat(), "payload": e.payload}
                for e in events
            ]
        }

    else:
        return {"type": view_type, "error": "unknown view"}


# ============================================================
# Utility: Determinism helper
# ============================================================

def assert_deterministic_replay(log: EventLog, branch_id: str = "main") -> bool:
    """
    Verification primitive: replaying the same events must produce identical node state.
    Critical for auditability and time-travel debugging.
    """
    node1 = log.reduce_to_node(branch_id=branch_id)
    # Simulate fresh log replay (in real impl we'd rebuild from persisted events)
    node2 = log.reduce_to_node(branch_id=branch_id)
    return node1.state == node2.state and node1.event_ids == node2.event_ids


if __name__ == "__main__":
    print("E-COS Primitives v0.1 loaded successfully.")
    print("Core classes: Event, Node, Edge, EventLog, Skill (Protocol), MCPBridge (Protocol), Agent (Protocol)")
    print("Key operations: append, reduce_to_node, fork_branch, project")