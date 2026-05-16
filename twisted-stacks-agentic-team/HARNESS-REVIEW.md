# AI Harness Review 2026: Best Practices for ARKITEKT

## Executive Summary
The harness is the moat. The model is commodity. This document synthesizes the best practices from leading AI harnesses (Archon, Hermes, OpenClaw, Agent Zero, Claude Code, Codex, LangGraph) to inform the development of ARKITEKT - our React Flow swarm command center.

## The Three Pillars of Harness Engineering
Every effective AI harness needs:
1. **Context Engineering** (CLAUDE.md, AGENTS.md, skills, ADRs)
2. **Architectural Constraints** (linters, dependency rules, test gates)
3. **Entropy Management** (loop detection, reasoning sandwiches, self-repair)

## Framework Comparison & Recommendations for ARKITEKT

### 1. Archon — Deterministic Workflow Harness
**Best for**: Repeatable AI coding workflows
**Key Features to Adopt**:
- Git worktree isolation for conflict-free parallel execution
- Composable nodes mixing deterministic bash/test/git with AI nodes
- YAML workflows: plan → implement → validate → review → PR
- Portable workflows in `.archon/workflows/` 
- Fire-and-forget execution with reviewed PR output
**Implementation**: Use for coding agents in the swarm needing repeatable PR workflows

### 2. Hermes Agent — Self-Improving Runtime
**Best for**: Automation that learns over time
**Key Features to Adopt**:
- Closed learning loop: autonomous SKILL.md creation after 5+ tool calls
- Three-layer memory: Session + FTS5 + Honcho user modeling
- Skill standard portable to Claude Code/Codex
- Cost arbitrage: route routine tasks to cheaper models
**Implementation**: Agent skill memory system for continuous improvement

### 3. OpenClaw — Orchestration Control Plane
**Best for**: Multi-channel agent organizations
**Key Features to Adopt**:
- 50+ platform integrations (Slack, Discord, Telegram, etc.)
- ClawHub marketplace for skill sharing
- Cross-session state and task handoff between agents
- Local-first, privacy-first, offline capable with Ollama
**Implementation**: Orchestration layer for agent team coordination

### 4. Agent Zero — Recursive Multi-Agent Sandbox
**Best for**: Deep autonomous execution with sandboxing
**Key Features to Adopt**:
- Hierarchical delegation with specialized subordinate agents
- Dockerized sandbox for safe code execution and browsing
- Autonomous tool creation rather than fixed registry
- Persistent memory with AI-filtered retrieval and auto-consolidation
- Private search via self-hosted SearXNG
- MCP + A2A for interoperability
**Implementation**: Execution runtime for agents needing deep sandboxed autonomy

### 5. LangGraph — Stateful Orchestration Framework
**Best for**: Custom agent products requiring auditability
**Key Features to Adopt**:
- Explicit graph model with conditional edges
- Checkpointing and time-travel debugging
- Human-in-the-loop capabilities
- Deep observability integration
- Python + JS/TypeScript SDKs
**Implementation**: Orchestration graph layer (nodes = agents, edges = handoffs)

## Recommended ARKITEKT Architecture
Combining the best of all worlds:

```
[User Interface] 
        ↓
[Orchestration Layer] ← LangGraph/OpenClaw 
        ↓
[Execution Runtime] ← Agent Zero (for deep autonomy) 
                      Hermes   (for learning agents) 
                      Archon   (for deterministic workflows)
        ↓
[Agent Team] ← Specialized agents with:
               - Context engineering (AGENTS.md, skills)
               - Tool usage standards
               - Heartbeat monitoring
               - Vectorized knowledge access
        ↓
[Memory & Vector Systems]
        ↓
[Tool Ecosystem]
```

## Context Engineering Standards

### AGENTS.md Format (2026 Standard)
```
# 🎭 [Agent Team Name]

## Agent [ID]: [Name] [Emoji]
- **Roll**: [Role description]
- **Färdigheter**: [Key skills]
- **Minnes-fokus**: [Memory focus areas]
- **Qdrant Collection**: `[collection_name]`

## Core Directives
```
[Behavioral guidelines and primary objectives]
```

## Memory System
- **Working Memory**: `./memory/working/[agent-id]/`
- **Long-Term Memory**: `./memory/long-term/[agent-id]/`
- **Episodic Memory**: `./memory/episodic/[agent-id]/`

## Tool Usage
[Reference to tool definitions in ./tools/]

## Heartbeat Protocol
- Interval: [seconds]
- Signal location: `./system/heartbeat/[agent-id].json`
- Escalation: [1=warning, 2=flag, 3=unresponsive]

## Vectorized Context
- Collection: `./vector/embeddings/[collection-name]/`
- Chunking strategy: [semantic/blocks/functions]
- Retrieval: [hybrid search parameters]
```

### Skill Format (agentskills.io compliant)
See: `./templates/skill.md`

### CLAUDE.md / PROJECT.md
Persistent project instructions and architectural decisions.

## Architectural Constraints

### Linters & Rules
- ESLint/Prettier for JavaScript/TypeScript
- Ruff for Python
- Custom rules for agent communication patterns
- Dependency vulnerability scanning

### Test Gates
- Unit tests for agent logic
- Integration tests for agent handoffs
- Property-based testing for edge cases
- Contract testing for tool interfaces

### Resource Limits
- CPU/memory limits per agent
- API rate limiting
- Tool execution timeouts
- Concurrent agent limits

## Entropy Management

### Loop Detection
- Recursive call detection with depth limits
- Repeated action identification
- Stuck state recognition (no progress over N cycles)

### Reasoning Sandwiches
- Thought → Action → Observation → Thought pattern
- Forced reflection after tool use
- Pre-action planning and post-action review

### Self-Repair Mechanisms
- Automatic retry with exponential backoff
- Fallback tool selection
- Error explanation and correction attempts
- Human-in-the-loop for persistent failures

## Implementation Roadmap

### Phase 1: Foundation
- [ ] Agent template standardization
- [ ] Memory system implementation
- [ ] Tool interface definition
- [ ] Heartbeat monitoring

### Phase 2: Context Engineering
- [ ] AGENTS.md format adoption
- [ ] Skill system implementation
- [ ] Vectorization pipeline
- [ ] Context compression

### Phase 3: Orchestration
- [ ] LangGraph/OpenClaw integration layer
- [ ] Inter-agent communication protocols
- [ ] Task distribution system
- [ ] Conflict resolution

### Phase 4: Learning & Improvement
- [ ] Closed learning loop (Hermes-style)
- [ ] Autonomous skill creation
- [ ] Performance metrics and optimization
- [ ] Cost-aware model routing

### Phase 5: Advanced Features
- [ ] Agent Zero sandbox execution
- [ ] Archon deterministic workflows
- [ ] Multi-platform gateway (OpenClaw)
- [ ] Observatory and debugging tools

## Immediate Next Steps for ARKITEKT

1. **Adopt the 2026 AGENTS.md format** for all agents
2. **Implement tool usage standards** with clear markdown documentation
3. **Add memory systems** (working, long-term, episodic) for each agent
4. **Create vectorization pipeline** for codebase understanding
5. **Establish heartbeat monitoring** for agent liveness
6. **Define architectural constraints** (linters, test gates, resource limits)
7. **Implement entropy management** (loop detection, reasoning sandwiches)
8. **Build skill memory system** for self-improvement

## References
- Archon: https://github.com/coleam00/Archon
- Hermes Agent: https://hermes-agent.nousresearch.com
- OpenClaw: https://openclaw.dev
- Agent Zero: https://agent-zero.ai
- Claude Code: https://claude.ai/code
- OpenAI Codex: https://openai.com/index/openai-codex/
- LangGraph: https://langchain-ai.github.io/langgraph/

---
*This document synthesizes the state of AI harness engineering as of 2026 to guide the development of ARKITEKT as a production-ready agentic system.*