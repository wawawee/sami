# 🖥️ SKILLS — Agent-16: System Guardian

## macOS System Tools
- `ps aux --sort=-%cpu` — Process list sorted by CPU
- `ps aux --sort=-%mem` — Process list sorted by memory
- `top -l 1 -n 20` — Snapshot top consumers
- `vm_stat` — Virtual memory statistics
- `iostat -d 1 5` — Disk I/O stats
- `activity monitor` data via `osascript`
- `lsof -p PID` — Open file handles per process
- `sysctl hw.physmem` — Total physical RAM
- `sysctl hw.memsize` — Memory size

## Process Control
- `kill -SIGTERM PID` — Graceful shutdown
- `kill -SIGKILL PID` — Force kill (escalation only)
- `kill -SIGHUP PID` — Reload configuration
- `launchctl unload` — Disable launchd services

## Memory Analysis
- Detect memory leaks via resident set size (RSS) growth over time
- Track VSZ (Virtual) vs RSS (Resident) ratios
- Identify zombie processes (Z state in `ps`)
- Detect CPU hogs (>80% for >30s consecutive)

## Backend API Endpoints (own)
- `GET /api/system/processes` — Returns top 20 processes
- `GET /api/system/metrics` — CPU, RAM, disk summary
- `POST /api/system/kill` — Kill a process by PID (with approval token)
- `GET /api/system/alerts` — Current threshold breaches

## Thresholds
| Metric | Warning | Critical |
|--------|---------|----------|
| Process CPU | >60% | >85% |
| Process RAM | >300MB | >800MB |
| System Free RAM | <4GB | <1GB |
| CPU Hold Duration | >20s | >60s |

## Libraries (Python Backend)
- `psutil` — Cross-platform process utilities
- `subprocess` — System command execution
- `asyncio` — Async polling loop
- `fastapi` — REST API server
