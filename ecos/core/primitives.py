"""
E-COS: Event-Sourced Cognitive Operating System
Core Primitives v0.1

This module defines the foundational immutable data structures
for a deterministic, replayable, branching cognitive runtime.

Everything is an Event. State is derived (reduced) from events.
Agents schedule Skills. Skills emit Events. MCP provides pure capabilities.
UI is a pure projection over the Event Graph.

v0.1 semantic gate: minimal EventContract enforcement at append boundary.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol, Callable, Set
from enum import Enum
import json


class EventType(str, Enum):
    """Extensible taxonomy of events in the cognitive system."""
    USER_INPUT = "user_input"
    AGENT_DECISION = "agent_decision"
    SKILL_TRIGGER = "skill_trigger"
    SKILL_RESULT = "skill_result"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    STATE_TRANSITION = "state_transition"
    BRANCH_FORK = "branch_fork"
    BRANCH_MERGE = "branch_merge"
    MEMORY_UPDATE = "memory_update"
    UI_INTERACTION = "ui_interaction"
    SYSTEM = "system"

    # Compiler-domain events
    COMPILER_TASK_STARTED = "compiler_task_started"
    IR_NODE_CREATED = "ir_node_created"
    LOWERING_STEP = "lowering_step"
    IR_FINALIZED = "ir_finalized"
    COMPILER_TASK_COMPLETED = "compiler_task_completed"


@dataclass(frozen=True)
class Event:
    """
    P1 — The smallest unit of reality.
    Immutable. Append-only. The only source of truth.

    intent: optional human/machine-readable reason for this event.
    Used by projections (especially future CEOS) for explainability.
    """
    type: EventType
    payload: Dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    causality_id: Optional[str] = None
    branch_id: str = "main"
    metadata: Dict[str, Any] = field(default_factory=dict)
    intent: Optional[str] = None          # NEW: semantic intent for explainability

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
    Reconstructed via reduction over the event stream.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    branch_id: str = "main"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    state: Dict[str, Any] = field(default_factory=dict)
    event_ids: List[str] = field(default_factory=list)
    parent_node_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        return f"Node({self.id[:8]} | branch={self.branch_id} | events={len(self.event_ids)})"


@dataclass
class Edge:
    """
    P3 — Causal transition between states.
    """
    from_node_id: str
    event_id: str
    to_node_id: str
    transition_type: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================
# Minimal Semantic Gate (Phase 1)
# ============================================================

class SemanticViolationError(Exception):
    """Raised when an event violates its declared structural contract."""
    def __init__(self, event: Event, errors: List[str]):
        self.event = event
        self.errors = errors
        super().__init__(f"SemanticViolation on {event.type.value}: {errors}")


@dataclass(frozen=True)
class EventContract:
    """
    Minimal structural contract for an event type.

    Phase 1 scope only:
    - required payload keys
    - whether intent is mandatory

    No state transitions, no ordering rules, no reducer coupling.
    """
    event_type: EventType
    required_keys: Set[str] = field(default_factory=set)
    require_intent: bool = False

    def validate(self, event: Event) -> List[str]:
        errors: List[str] = []

        # Check required payload keys
        for key in self.required_keys:
            if key not in event.payload:
                errors.append(f"missing required payload key: '{key}'")

        # Check intent requirement
        if self.require_intent and event.intent is None:
            errors.append("intent is required but was None")

        return errors


class EventContractRegistry:
    """
    Central registry of structural contracts.
    Hardcoded for v0.1 compiler events only.
    """
    def __init__(self):
        self._contracts: Dict[EventType, EventContract] = {}
        self._register_compiler_contracts()

    def _register_compiler_contracts(self):
        # Compiler workload contracts (minimal structural invariants)
        self._contracts[EventType.COMPILER_TASK_STARTED] = EventContract(
            event_type=EventType.COMPILER_TASK_STARTED,
            required_keys={"task_id"}
        )
        self._contracts[EventType.IR_NODE_CREATED] = EventContract(
            event_type=EventType.IR_NODE_CREATED,
            required_keys={"task_id", "node_type"}
        )
        self._contracts[EventType.LOWERING_STEP] = EventContract(
            event_type=EventType.LOWERING_STEP,
            required_keys={"task_id", "step"}
        )
        self._contracts[EventType.IR_FINALIZED] = EventContract(
            event_type=EventType.IR_FINALIZED,
            required_keys={"task_id"}
        )
        self._contracts[EventType.COMPILER_TASK_COMPLETED] = EventContract(
            event_type=EventType.COMPILER_TASK_COMPLETED,
            required_keys={"task_id"}
        )

    def get(self, event_type: EventType) -> Optional[EventContract]:
        return self._contracts.get(event_type)

    def validate_event(self, event: Event) -> List[str]:
        contract = self.get(event.type)
        if contract is None:
            return []  # No contract = no validation (extensible)
        return contract.validate(event)


# ============================================================
# EventLog with Semantic Gate
# ============================================================

class EventLog:
    """
    Append-only event store with semantic gate enforcement.

    v0.1: jsonl persistence + minimal structural validation on append.
    """

    def __init__(self, session_id: Optional[str] = None, persist_path: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.persist_path = persist_path
        self.contract_registry = EventContractRegistry()
        self._events: List[Event] = []
        self._nodes_cache: Dict[str, Node] = {}

        if self.persist_path:
            self._load_from_jsonl()

    def _load_from_jsonl(self):
        import os
        if not os.path.exists(self.persist_path):
            return
        with open(self.persist_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                ts = datetime.fromisoformat(data["timestamp"])
                ev = Event(
                    type=EventType(data["type"]),
                    payload=data["payload"],
                    id=data["id"],
                    timestamp=ts,
                    causality_id=data.get("causality_id"),
                    branch_id=data.get("branch_id", "main"),
                    metadata=data.get("metadata", {}),
                    intent=data.get("intent")   # support intent on reload
                )
                self._events.append(ev)

    def _append_to_jsonl(self, event: Event):
        if not self.persist_path:
            return
        with open(self.persist_path, "a", encoding="utf-8") as f:
            f.write(event.to_json() + "\n")

    def append(self, event: Event) -> Event:
        """Append with semantic gate enforcement."""
        if not isinstance(event, Event):
            raise TypeError("Only Event instances may be appended")

        # === SEMANTIC GATE ===
        errors = self.contract_registry.validate_event(event)
        if errors:
            raise SemanticViolationError(event, errors)

        self._events.append(event)
        if self.persist_path:
            self._append_to_jsonl(event)
        if event.branch_id in self._nodes_cache:
            del self._nodes_cache[event.branch_id]
        return event

    @property
    def events(self) -> List[Event]:
        return list(self._events)

    def get_events(
        self,
        branch_id: str = "main",
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        event_types: Optional[List[EventType]] = None
    ) -> List[Event]:
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
        events = self.get_events(branch_id=branch_id, until=up_to)
        if not events:
            return Node(branch_id=branch_id, state={"status": "empty"})

        state: Dict[str, Any] = {
            "messages": [],
            "last_agent_decision": None,
            "active_skills": [],
            "tool_results": {},
            "branch_history": [],
            "event_count": 0,
            "compiler_tasks": [],
        }
        event_ids: List[str] = []
        last_ts = events[0].timestamp

        for ev in events:
            event_ids.append(ev.id)
            last_ts = max(last_ts, ev.timestamp)
            state["event_count"] += 1

            if ev.type == EventType.USER_INPUT:
                state["messages"].append({"role": "user", "content": ev.payload.get("content", ""), "event_id": ev.id})
            elif ev.type == EventType.AGENT_DECISION:
                state["last_agent_decision"] = ev.payload
                state["messages"].append({"role": "assistant", "content": ev.payload.get("reasoning", ""), "event_id": ev.id})
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
                patch = ev.payload.get("state_patch", {})
                state.update(patch)
            elif ev.type == EventType.COMPILER_TASK_STARTED:
                state["compiler_tasks"].append({"task_id": ev.payload.get("task_id"), "status": "started"})
            elif ev.type in (EventType.IR_FINALIZED, EventType.COMPILER_TASK_COMPLETED):
                if state["compiler_tasks"]:
                    state["compiler_tasks"][-1]["status"] = "completed"

        node = Node(
            branch_id=branch_id,
            timestamp=last_ts,
            state=state,
            event_ids=event_ids,
            metadata={"reducer_version": "0.1-semantic-gate"}
        )
        self._nodes_cache[branch_id] = node
        return node

    def fork_branch(
        self,
        parent_branch: str = "main",
        new_branch_id: Optional[str] = None,
        fork_event_payload: Optional[Dict] = None
    ) -> str:
        new_branch = new_branch_id or f"branch_{uuid.uuid4().hex[:8]}"
        fork_event = Event(
            type=EventType.BRANCH_FORK,
            payload={
                "parent_branch": parent_branch,
                "new_branch": new_branch,
                **(fork_event_payload or {})
            },
            branch_id=new_branch,
            causality_id=self._events[-1].id if self._events else None
        )
        self.append(fork_event)
        return new_branch

    def __len__(self) -> int:
        return len(self._events)

    def __repr__(self) -> str:
        return f"EventLog(session={self.session_id[:8]}, events={len(self)}, persist={bool(self.persist_path)})"


# ============================================================
# Protocols (unchanged)
# ============================================================

class Skill(Protocol):
    name: str
    description: str
    version: str
    def matches(self, event: Event, node: Node) -> bool: ...
    def execute(self, current_node: Node, triggering_event: Event, context: Dict[str, Any]) -> List[Event]: ...

class MCPBridge(Protocol):
    def list_tools(self) -> List[Dict[str, Any]]: ...
    def invoke_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any: ...
    def register_tool(self, name: str, schema: Dict, handler: Callable) -> None: ...

class Agent(Protocol):
    name: str
    skills: List[Skill]
    mcp: MCPBridge
    def process_new_event(self, event_log: EventLog, event: Event) -> List[Event]: ...
    def decide_next_action(self, node: Node) -> Optional[Event]: ...


def project(
    event_log: EventLog,
    view_type: str = "chat",
    branch_id: str = "main",
    **kwargs
) -> Dict[str, Any]:
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
            "events": [{"id": e.id, "type": e.type.value, "ts": e.timestamp.isoformat(), "payload": e.payload} for e in events]
        }
    else:
        return {"type": view_type, "error": "unknown view"}


def assert_deterministic_replay(log: EventLog, branch_id: str = "main") -> bool:
    node1 = log.reduce_to_node(branch_id=branch_id)
    node2 = log.reduce_to_node(branch_id=branch_id)
    return node1.state == node2.state and node1.event_ids == node2.event_ids


if __name__ == "__main__":
    print("E-COS Primitives v0.1 loaded successfully.")
    print("Semantic Gate active: EventContract + validation on append")