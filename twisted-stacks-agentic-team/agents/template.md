# Agent Template (2026 Standard)

## Metadata
- **Agent ID**: `[ID]` (e.g., 01)
- **Name**: `[Agent Name]`
- **Codename**: `[CODENAME]`
- **Role**: `[Role Description]`
- **Version**: `1.0.0`
- **Created**: `YYYY-MM-DD`
- **Last Updated**: `YYYY-MM-DD`
- **Status**: `active|inactive|maintenance`
- **Heartbeat Interval**: `[seconds]` (default: 30)

## Core Directives
```
[Primary objective and behavioral guidelines for the agent]
```

## Capabilities
- **Tools**: `[List of tool categories this agent can use]`
- **Knowledge Domains**: `[Areas of expertise]`
- **Communication Protocols**: `[How this agent interacts with others]`

## Memory System
### Working Memory
- Short-term context for current task (token-limited)
- Stored in: `./memory/working/[agent-id]/`

### Long-Term Memory
- Persistent knowledge base
- Stored in: `./memory/long-term/[agent-id]/`
- Vectorized for retrieval: `./vector/embeddings/[agent-id]/`

### Episodic Memory
- Task execution history
- Stored in: `./memory/episodic/[agent-id]/`

## Tool Usage Standards
All tools must follow the interface:
```
tool_name:
  description: "What the tool does"
  parameters:
    param1: {type: "string", description: "..."}
    param2: {type: "number", description: "..."}
  returns: {type: "object", description: "..."}
  side_effects: ["list", "of", "possible", "side", "effects"]
  async: [true/false]
  timeout: [seconds] (optional)
```

Example tool call in agent logic:
```python
# Pseudocode for agent tool usage
result = await use_tool(
    "web_search",
    {
        "query": "latest developments in agentic systems",
        "max_results": 5
    }
)
```

## Heartbeat Protocol
- Agents must signal liveness every `[heartbeat_interval]` seconds
- Heartbeat signal includes:
  - Agent ID
  - Timestamp
  - Current status (idle, working, error)
  - Resource usage (CPU, memory) - optional
  - Last completed action
- Missed heartbeats trigger escalation:
  - 1 missed: Warning log
  - 2 missed: Agent flagged for check
  - 3 missed: Agent considered unresponsive, orchestrator notified

## Vectorized Context Loading
For efficient operation within token limits:
1. Codebase is pre-processed into semantic chunks
2. Each chunk is embedded and stored in vector database
3. Agent retrieves only relevant chunks based on current task
4. Chunks are re-ranked by relevance and recency
5. Final context is compressed to fit within model's context window

Vectorization process:
- Files are parsed by language-appropriate parser
- Content is split into semantic chunks (functions, classes, blocks)
- Each chunk gets metadata: file path, line numbers, symbols
- Embeddings generated using: `[embedding model]`
- Stored in: `./vector/index/[collection-name]`

## Example Agent Implementation
See: `./agents/example-agent.md` for a complete implementation.

## Related Files
- Tool definitions: `./tools/`
- Memory schemas: `./memory/schemas/`
- Vector config: `./vector/config/`
- Heartbeat monitor: `./system/heartbeat-monitor.py`