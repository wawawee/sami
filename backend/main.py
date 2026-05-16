from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psutil
import platform
import subprocess
import signal
import os, json
import asyncio
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from free_gateway import FreeGateway
from agent_orchestrator import AgentOrchestrator, AGENT_DEFS

gateway = FreeGateway()
orchestrator = AgentOrchestrator(gateway)

app = FastAPI(title="ANLAGSTAVLAN Agentic API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ANLAGSTAVLAN API",
        "version": "2.0.0",
        "agents": 16,
        "timestamp": datetime.utcnow().isoformat()
    }

# ─────────────────────────────────────────────────────────────
# Agents
# ─────────────────────────────────────────────────────────────
@app.get("/agents")
async def get_agents():
    return [
        {"id": "01", "name": "Scout", "codename": "SCOUT", "role": "Researcher", "collection": "research_memories"},
        {"id": "02", "name": "Blueprint", "codename": "BLUEPRINT", "role": "Architect", "collection": "architecture_memories"},
        {"id": "03", "name": "Forge", "codename": "FORGE", "role": "Code Writer", "collection": "code_memories"},
        {"id": "04", "name": "Hammer", "codename": "HAMMER", "role": "QA Engineer", "collection": "qa_memories"},
        {"id": "05", "name": "Aegis", "codename": "AEGIS", "role": "Security Sentinel", "collection": "security_memories"},
        {"id": "06", "name": "Pipeline", "codename": "PIPELINE", "role": "Data Engineer", "collection": "data_memories"},
        {"id": "07", "name": "Launcher", "codename": "LAUNCHER", "role": "DevOps Runner", "collection": "devops_memories"},
        {"id": "08", "name": "Canvas", "codename": "CANVAS", "role": "UX Designer", "collection": "ux_memories"},
        {"id": "09", "name": "Scribe", "codename": "SCRIBE", "role": "Technical Writer", "collection": "docs_memories"},
        {"id": "10", "name": "Tracer", "codename": "TRACER", "role": "Debugger", "collection": "debug_memories"},
        {"id": "11", "name": "Turbo", "codename": "TURBO", "role": "Performance Tuner", "collection": "performance_memories"},
        {"id": "12", "name": "Bridge", "codename": "BRIDGE", "role": "Integration Specialist", "collection": "integration_memories"},
        {"id": "13", "name": "Maestro", "codename": "MAESTRO", "role": "Orchestrator", "collection": "orchestrator_memories"},
        {"id": "14", "name": "Packager", "codename": "PACKAGER", "role": "Package Manager", "collection": "package_memories"},
        {"id": "15", "name": "Inspector", "codename": "INSPECTOR", "role": "Examination Agent", "collection": "examination_memories"},
        {"id": "16", "name": "Watchdog", "codename": "WATCHDOG", "role": "System Guardian", "collection": "system_memories"},
    ]

# ─────────────────────────────────────────────────────────────
# System Monitor (Agent-16: WATCHDOG)
# ─────────────────────────────────────────────────────────────
def bytes_to_mb(b: int) -> float:
    return round(b / (1024 * 1024), 1)

@app.get("/api/system/metrics")
async def get_system_metrics():
    """
    WATCHDOG: Real-time macOS system resource snapshot.
    Returns top 20 processes by CPU, plus overall system stats.
    """
    cpu_percent = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'username', 'status', 'create_time']):
        try:
            info = proc.info
            if info['memory_info'] is None:
                continue
            processes.append({
                "pid": info['pid'],
                "name": info['name'] or "unknown",
                "cpu": round(info['cpu_percent'] or 0, 1),
                "memory_mb": bytes_to_mb(info['memory_info'].rss),
                "vsz_mb": bytes_to_mb(info['memory_info'].vms),
                "user": info['username'] or "system",
                "status": info['status'] or "unknown",
                "started": datetime.fromtimestamp(info['create_time']).strftime('%H:%M:%S') if info.get('create_time') else "?",
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Sort by CPU then memory
    top_by_cpu = sorted(processes, key=lambda x: x['cpu'], reverse=True)[:20]

    # Build alerts
    alerts = []
    for p in top_by_cpu:
        if p['cpu'] > 85:
            alerts.append({"pid": p['pid'], "name": p['name'], "reason": f"CPU {p['cpu']}% — critical threshold", "severity": "critical"})
        elif p['cpu'] > 60:
            alerts.append({"pid": p['pid'], "name": p['name'], "reason": f"CPU {p['cpu']}% — warning threshold", "severity": "warn"})
        if p['memory_mb'] > 800:
            alerts.append({"pid": p['pid'], "name": p['name'], "reason": f"RAM {p['memory_mb']}MB — critical threshold", "severity": "critical"})
        elif p['memory_mb'] > 300:
            alerts.append({"pid": p['pid'], "name": p['name'], "reason": f"RAM {p['memory_mb']}MB — warning threshold", "severity": "warn"})

    return {
        "cpu_percent": cpu_percent,
        "total_ram_mb": bytes_to_mb(mem.total),
        "free_ram_mb": bytes_to_mb(mem.available),
        "used_ram_pct": mem.percent,
        "disk_total_gb": round(disk.total / (1024**3), 1),
        "disk_free_gb": round(disk.free / (1024**3), 1),
        "disk_used_pct": disk.percent,
        "platform": platform.platform(),
        "processes": top_by_cpu,
        "alerts": alerts[:10],
        "timestamp": datetime.utcnow().isoformat(),
    }

class KillRequest(BaseModel):
    pid: int
    signal_type: str = "SIGTERM"  # SIGTERM or SIGKILL
    reason: str = "User requested"

@app.post("/api/system/kill")
async def kill_process(req: KillRequest):
    """
    WATCHDOG: Kill a process by PID.
    SIGTERM first (graceful), then SIGKILL if needed.
    Requires orchestrator approval token in production.
    """
    pid = req.pid

    # Safety: never kill system processes
    if pid <= 100:
        raise HTTPException(status_code=403, detail="Cannot kill system processes (PID ≤ 100)")
    if pid == os.getpid():
        raise HTTPException(status_code=403, detail="Cannot kill self")

    try:
        proc = psutil.Process(pid)
        name = proc.name()

        if req.signal_type == "SIGKILL":
            proc.kill()
        else:
            proc.terminate()
            # Wait up to 5s then force kill
            try:
                proc.wait(timeout=5)
            except psutil.TimeoutExpired:
                proc.kill()

        return {
            "success": True,
            "pid": pid,
            "name": name,
            "signal": req.signal_type,
            "reason": req.reason,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Process '{name}' (PID {pid}) terminated successfully"
        }
    except psutil.NoSuchProcess:
        raise HTTPException(status_code=404, detail=f"Process {pid} not found")
    except psutil.AccessDenied:
        raise HTTPException(status_code=403, detail=f"Access denied for process {pid}")

@app.get("/api/system/processes")
async def get_top_processes():
    """Top 20 processes sorted by RAM usage."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'username', 'status']):
        try:
            info = proc.info
            if info['memory_info'] is None:
                continue
            processes.append({
                "pid": info['pid'],
                "name": info['name'],
                "cpu": round(info['cpu_percent'] or 0, 1),
                "memory_mb": bytes_to_mb(info['memory_info'].rss),
                "user": info['username'] or "system",
                "status": info['status'],
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return sorted(processes, key=lambda x: x['memory_mb'], reverse=True)[:20]

# ─────────────────────────────────────────────────────────────
# Terminal Command Execution
# ─────────────────────────────────────────────────────────────
class TerminalCommand(BaseModel):
    command: str
    timeout: int = 30

@app.post("/api/terminal/execute")
async def execute_terminal(cmd: TerminalCommand):
    project_root = Path(__file__).parent.parent
    try:
        process = await asyncio.create_subprocess_shell(
            cmd.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(project_root),
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=cmd.timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            return {
                "output": f"[TIMEOUT] Command exceeded {cmd.timeout}s limit",
                "stderr": "",
                "exit_code": -1,
            }

        return {
            "output": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
            "exit_code": process.returncode,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─────────────────────────────────────────────────────────────
# Agent Execution
# ─────────────────────────────────────────────────────────────
class AgentTask(BaseModel):
    agent_id: str
    task: str
    model: str = ""

class WorkflowRequest(BaseModel):
    tasks: list[AgentTask]

class AgentResponse(BaseModel):
    agent_id: str
    result: str
    turns: int
    error: str = ""

ws_connections: dict[str, list[WebSocket]] = {}

async def broadcast(agent_id: str, event: dict):
    for ws in ws_connections.get(agent_id, []):
        try:
            await ws.send_json(event)
        except Exception:
            pass
    for ws in ws_connections.get("_all", []):
        try:
            await ws.send_json(event)
        except Exception:
            pass

@orchestrator.on_event
async def handle_orchestrator_event(event: dict):
    agent_id = event.get("agent_id", "system")
    await broadcast(agent_id, event)

@app.websocket("/api/ws/agents")
async def agent_websocket(ws: WebSocket):
    await ws.accept()
    agent_id = "_all"
    try:
        data = await ws.receive_text()
        try:
            payload = json.loads(data)
            if "agent_id" in payload:
                agent_id = payload["agent_id"]
        except json.JSONDecodeError:
            pass
    except Exception:
        pass

    if agent_id not in ws_connections:
        ws_connections[agent_id] = []
    ws_connections[agent_id].append(ws)

    try:
        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("action") == "execute":
                    asyncio.create_task(orchestrator.execute(msg["agent_id"], msg["task"]))
                elif msg.get("action") == "stop":
                    orchestrator.stop()
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        if agent_id in ws_connections:
            ws_connections[agent_id] = [w for w in ws_connections[agent_id] if w != ws]

@app.post("/api/agents/execute")
async def execute_agent(req: AgentTask):
    result = await orchestrator.execute(req.agent_id, req.task)
    return result

@app.post("/api/agents/workflow")
async def execute_workflow(req: WorkflowRequest):
    tasks = [{"agent_id": t.agent_id, "task": t.task} for t in req.tasks]
    result = await orchestrator.workflow(tasks)
    return result

@app.post("/api/agents/stop")
async def stop_agents():
    orchestrator.stop()
    return {"status": "stopped"}

# ─────────────────────────────────────────────────────────────
# Config endpoint for frontend
# ─────────────────────────────────────────────────────────────
@app.get("/api/config")
async def get_config():
    return {
        "gateway": {
            "openrouter": bool(os.getenv("OPENROUTER_API_KEY")),
            "gemini": bool(os.getenv("GEMINI_API_KEY")),
        },
        "agents": len(AGENT_DEFS),
        "ws_endpoint": "/api/ws/agents",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
