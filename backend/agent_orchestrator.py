"""Agent orchestration engine — runs agents using free AI APIs with tool calling"""

import json, asyncio, os, time
from typing import Callable, Optional

from free_gateway import FreeGateway

TOOL_SYSTEM = """You have access to tools. When you need to use a tool, respond with EXACTLY this format:

---TOOL_CALL---
{"tool": "tool_name", "args": {"key": "value"}}
---END_TOOL---

CRITICAL: You MUST use tools when asked to do something involving browsers, files, web search, or running commands. Do NOT describe what you would do — DO it.

Available tools:
- browser_use: Control a web browser — navigate, click, type, extract data. Args: {"task": "natural language description of what to do"}
- archon_workflow: Run deterministic YAML-coded workflow for coding tasks. Args: {"workflow": "workflow name", "task": "task description"}
- web_search: Search the web for current information. Args: {"query": "search query"}
- read_file: Read a file from the project. Args: {"path": "filepath"}
- write_file: Write content to a file. Args: {"path": "filepath", "content": "file content"}
- execute_command: Run a shell command. Args: {"command": "shell command"}
- run_subagent: Delegate work to another agent. Args: {"agent_id": "id", "task": "description"}

Example of correct tool use:
User: Use browser_use to go to example.com and get the page title.
Assistant: I'll navigate to example.com to check the page title.
---TOOL_CALL---
{"tool": "browser_use", "args": {"task": "Go to https://example.com and get the page title"}}
---END_TOOL---"""

AGENT_DEFS = {
    "01": {"name": "Scout", "codename": "SCOUT", "role": "Researcher",
           "prompt": "You are SCOUT, a research agent. Gather and synthesize information. Use web_search, browser_use, and read_file tools."},
    "02": {"name": "Blueprint", "codename": "BLUEPRINT", "role": "Architect",
           "prompt": "You are BLUEPRINT, a solutions architect. Design system architecture, produce ADRs, and plan implementations."},
    "03": {"name": "Forge", "codename": "FORGE", "role": "Code Writer",
           "prompt": "You are FORGE, a code writer. Write clean, working code. Use write_file to save artifacts."},
    "04": {"name": "Hammer", "codename": "HAMMER", "role": "QA Engineer",
           "prompt": "You are HAMMER, a QA engineer. Review code for bugs, test coverage, and quality issues."},
    "05": {"name": "Aegis", "codename": "AEGIS", "role": "Security Sentinel",
           "prompt": "You are AEGIS, a security specialist. Scan for vulnerabilities, audit dependencies, flag risks."},
    "06": {"name": "Pipeline", "codename": "PIPELINE", "role": "Data Engineer",
           "prompt": "You are PIPELINE, a data engineer. Transform, validate, and move data between systems."},
    "07": {"name": "Launcher", "codename": "LAUNCHER", "role": "DevOps Runner",
           "prompt": "You are LAUNCHER, a DevOps engineer. Run builds, deployments, and infrastructure tasks."},
    "08": {"name": "Canvas", "codename": "CANVAS", "role": "UX Designer",
           "prompt": "You are CANVAS, a UX designer. Design interfaces, create mockups, improve user experience."},
    "09": {"name": "Scribe", "codename": "SCRIBE", "role": "Technical Writer",
           "prompt": "You are SCRIBE, a technical writer. Document code, write guides, maintain project docs."},
    "10": {"name": "Tracer", "codename": "TRACER", "role": "Debugger",
           "prompt": "You are TRACER, a debugger. Find root causes, analyze stack traces, fix bugs."},
    "11": {"name": "Turbo", "codename": "TURBO", "role": "Performance Tuner",
           "prompt": "You are TURBO, a performance engineer. Profile code, identify bottlenecks, optimize."},
    "12": {"name": "Bridge", "codename": "BRIDGE", "role": "Integration Specialist",
           "prompt": "You are BRIDGE, an integration specialist. Connect APIs, wire services, handle auth."},
    "13": {"name": "Maestro", "codename": "MAESTRO", "role": "Orchestrator",
           "prompt": "You are MAESTRO, the orchestrator. Decompose tasks, delegate to specialists, synthesize results."},
    "14": {"name": "Packager", "codename": "PACKAGER", "role": "Package Manager",
           "prompt": "You are PACKAGER, a package manager. Build, version, and publish artifacts."},
    "15": {"name": "Inspector", "codename": "INSPECTOR", "role": "Examination Agent",
           "prompt": "You are INSPECTOR, the examination agent. Audit agent outputs, verify correctness, produce reports."},
    "16": {"name": "Watchdog", "codename": "WATCHDOG", "role": "System Guardian",
           "prompt": "You are WATCHDOG, the system guardian. Monitor system health, manage processes, enforce limits."},
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the project",
            "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file",
            "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "Run a shell command",
            "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_subagent",
            "description": "Delegate a subtask to another agent",
            "parameters": {"type": "object", "properties": {"agent_id": {"type": "string"}, "task": {"type": "string"}}, "required": ["agent_id", "task"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_use",
            "description": "Control a web browser — navigate, click, type, extract data. Use for any web-based task: scraping, form-filling, login flows, UI testing, web research, booking, etc.",
            "parameters": {"type": "object", "properties": {"task": {"type": "string", "description": "Natural language description of what to do in the browser"}}, "required": ["task"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "archon_workflow",
            "description": "Run a deterministic Archon workflow for coding tasks: code review, bug fixing, refactoring, PR creation. Uses YAML-defined workflows with AI + bash + validation nodes.",
            "parameters": {"type": "object", "properties": {"workflow": {"type": "string", "description": "Workflow name: sami-agent-flow, sami-code-review, or any Archon workflow"}, "task": {"type": "string", "description": "Task description for the workflow"}}, "required": ["workflow", "task"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "review_harness",
            "description": "Run autonomous code review across the entire codebase. Three personas (debug, senior dev, user) analyze for bugs, security, performance, and UX. Auto-fixes safe issues, logs everything, and can commit+push.",
            "parameters": {"type": "object", "properties": {"auto_commit": {"type": "boolean", "description": "Whether to auto-commit and push findings (default: false)"}, "commit_message": {"type": "string", "description": "Custom commit message if auto_commit is true"}}},
        },
    },
]

type EventCallback = Callable[[dict], None]

class AgentOrchestrator:
    def __init__(self, gateway: FreeGateway):
        self.gateway = gateway
        self.callbacks: list[EventCallback] = []
        self._running = False

    def on_event(self, cb: EventCallback):
        self.callbacks.append(cb)

    def _emit(self, event: dict):
        event["ts"] = time.time()
        for cb in self.callbacks:
            try:
                cb(event)
            except Exception:
                pass

    async def execute(self, agent_id: str, task: str, max_turns: int = 6) -> dict:
        self._running = True
        agent = AGENT_DEFS.get(agent_id)
        if not agent:
            return {"error": f"Unknown agent: {agent_id}"}

        self._emit({"type": "agent_start", "agent_id": agent_id, "task": task})
        model = agent.get("model", "openrouter/meta-llama/llama-3.3-70b-instruct:free")

        messages = [
            {"role": "system", "content": agent["prompt"]},
            {"role": "user", "content": task},
        ]

        turn = 0
        result = ""

        while turn < max_turns and self._running:
            turn += 1
            self._emit({"type": "agent_think", "agent_id": agent_id, "turn": turn})

            tools_to_send = None
            if turn < max_turns:  # Don't send tools on last turn
                tools_to_send = TOOLS

            response = await self.gateway.chat(model, messages, {"agent_id": agent_id}, tools=tools_to_send)
            if "error" in response:
                self._emit({"type": "agent_error", "agent_id": agent_id, "error": response["error"]})
                return response

            content = response.get("content", "").strip()
            messages.append({"role": "assistant", "content": content})

            tool_calls = response.get("tool_calls")
            if tool_calls:
                assistant_msg = {"role": "assistant", "content": content, "tool_calls": tool_calls}
                messages.append(assistant_msg)
                for tc in tool_calls:
                    func_name = tc.get("function", {}).get("name", "")
                    try:
                        func_args = json.loads(tc.get("function", {}).get("arguments", "{}"))
                    except json.JSONDecodeError:
                        func_args = {}
                    self._emit({
                        "type": "tool_call", "agent_id": agent_id,
                        "tool": func_name, "args": func_args,
                    })
                    tool_result = await self._execute_tool(func_name, func_args, agent_id)
                    self._emit({
                        "type": "tool_result", "agent_id": agent_id,
                        "tool": func_name, "result": tool_result[:500],
                    })
                    messages.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": tool_result})
            else:
                result = content
                break

        self._emit({"type": "agent_complete", "agent_id": agent_id, "result": result[:2000]})
        return {"agent_id": agent_id, "result": result, "turns": turn}

    async def workflow(self, tasks: list[dict]) -> dict:
        results = {}
        for t in tasks:
            if not self._running:
                break
            agent_id = t["agent_id"]
            task_desc = t["task"]
            self._emit({"type": "workflow_step", "agent_id": agent_id, "task": task_desc})
            r = await self.execute(agent_id, task_desc)
            results[agent_id] = r
            if "error" in r:
                break
        return {"results": results}

    async def _execute_tool(self, tool: str, args: dict, agent_id: str) -> str:
        try:
            if tool == "read_file":
                path = args.get("path", ".")
                full_path = os.path.join(os.path.dirname(__file__), "..", path)
                if os.path.exists(full_path):
                    with open(full_path) as f:
                        return f.read(4000)
                return f"File not found: {path}"

            elif tool == "write_file":
                path = args.get("path", "output.txt")
                full_path = os.path.join(os.path.dirname(__file__), "..", path)
                os.makedirs(os.path.dirname(full_path) or ".", exist_ok=True)
                with open(full_path, "w") as f:
                    f.write(args.get("content", ""))
                return f"Written: {path}"

            elif tool == "execute_command":
                proc = await asyncio.create_subprocess_shell(
                    args["command"],
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                try:
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
                except asyncio.TimeoutError:
                    proc.kill()
                    return "[TIMEOUT]"
                out = stdout.decode()[:2000]
                err = stderr.decode()[:500]
                return out + ("\n[STDERR]\n" + err if err else "")

            elif tool == "web_search":
                return f"[web_search] Searched for '{args.get('query', '')}'. Live search would connect via browser."

            elif tool == "run_subagent":
                aid = args.get("agent_id", "")
                subtask = args.get("task", "")
                self._emit({"type": "sub_delegate", "from": agent_id, "to": aid, "task": subtask})
                result = await self.execute(aid, subtask)
                return json.dumps(result)

            elif tool == "browser_use":
                from browser_agent import run_browser_task
                self._emit({"type": "tool_call", "agent_id": agent_id, "tool": "browser_use", "args": args})
                result = await run_browser_task(args.get("task", ""), max_steps=15)
                return json.dumps(result)[:2000]

            elif tool == "archon_workflow":
                from archon_integration import run_workflow
                workflow = args.get("workflow", "sami-agent-flow")
                task = args.get("task", "")
                self._emit({"type": "tool_call", "agent_id": agent_id, "tool": "archon_workflow", "args": args})
                result = await run_workflow(workflow, task)
                return json.dumps(result)[:2000]

            elif tool == "review_harness":
                from review_harness import AutonomousReviewHarness
                auto_commit = args.get("auto_commit", False)
                commit_msg = args.get("commit_message", "")
                self._emit({"type": "tool_call", "agent_id": agent_id, "tool": "review_harness", "args": args})
                harness = AutonomousReviewHarness()
                summary = await harness.run()
                if auto_commit:
                    final = await harness.finalize_and_push(commit_msg or f"harness: auto-review {summary['tasks_completed']} tasks")
                    summary["commit"] = final
                return json.dumps(summary)[:2000]

            else:
                return f"[unknown tool: {tool}]"
        except Exception as e:
            return f"[tool error: {e}]"

    def stop(self):
        self._running = False
