# E-COS: Event-Sourced Cognitive Operating System

**Version:** 0.1 (prototype foundations)

This is the concrete computational architecture distilled from the core primitives of cognition, agency, branching execution, skills, MCP, and projections.

## The 7 Primitives (implemented)

| Primitive | Implementation | Key Property |
|-----------|----------------|--------------|
| **P1 Event** | `Event` dataclass (frozen, immutable) | Smallest unit. Append-only. Has type, payload, timestamp, causality_id, branch_id |
| **P2 Node** | `Node` dataclass | Materialized state snapshot via `reduce()` over events. Never source of truth. |
| **P3 Edge** | `Edge` dataclass + implicit in EventLog | Causal link: Node --Event--> Node |
| **P4 Agent** | `Agent` Protocol | Scheduler / execution kernel. Observes events → runs Skills → emits new Events |
| **P5 Skill** | `Skill` Protocol | Deterministic cognition unit. `matches()` + `execute(current_node, event) -> List[Event]` |
| **P6 MCP** | `MCPBridge` Protocol | Pure capability/syscall layer. Zero state ownership. Tool discovery + invocation only. |
| **P7 Projection** | `project(event_log, view_type)` pure function | UI = rendering over the event graph. Chat, graph, timeline, debug replay, etc. |

## Core Innovation

**The Event Graph is the OS.**

- Single source of truth: the append-only `EventLog`
- State is always derived: `Node = reduce(EventLog, branch, time)`
- Branching = first-class execution forking (Git for thought)
- Deterministic replay & time-travel debugging built-in
- UI is a pure function (no hidden logic)
- Skills are compiled behavioral graphs, not ad-hoc functions
- Agents are schedulers, not tools or chatbots

## What this enables (today in v0.1)

- Fully deterministic agent behavior
- Parallel hypothesis exploration via cheap forks
- Complete audit trail of every decision and tool use
- "Time travel" to any previous cognitive state
- Multiple UI projections from the same truth (chat + graph + execution trace)
- Safe multi-agent concurrency (conflict resolution via event ordering + branches)

## Running the Demo

From the repository root (after cloning):

```bash
PYTHONPATH=. python -m ecos.examples.demo_branching
```

Or install in editable mode:

```bash
pip install -e .
python -m ecos.examples.demo_branching
```

It demonstrates:
1. Seeding events on `main`
2. Reducing to `Node`
3. Forking into `research_strategy_A` and `research_strategy_B`
4. Independent evolution on each branch
5. Divergent states
6. Pure projections (chat / timeline)
7. Determinism verification (`assert_deterministic_replay`)
8. Basic time-travel reduction

## Next Directions (as discussed)

- **Option A (done)**: Exact schemas + runnable core (this)
- **Option B**: MCP hooks into event transitions safely
- **Option C**: Skill compilation into deterministic execution graphs (e.g. rule-based or graph-compiled skills)
- **Option D**: 30-60 day MVP architecture (full minimal Agent + 2-3 Skills + stub MCP + OpenWebUI-like projection server)

## Philosophy

> Thoughts are events.  
> Reasoning is graph traversal.  
> Tools are system calls (via MCP).  
> UI is a debugger for intelligence.  
> The entire history is replayable and branchable.

This is not a framework.  
This is a **cognitive operating system**.

---

*Built as a direct implementation of the unified model you synthesized.*