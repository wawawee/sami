#!/usr/bin/env python3
"""
Heartbeat Monitor for Twisted Stacks Agentic Team
Monitors agent liveness and handles escalation procedures
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Configuration
HEARTBEAT_DIR = Path("./system/heartbeat")
AGENTS_CONFIG = {
    "01": {"name": "Scout", "interval": 30},
    "02": {"name": "Blueprint", "interval": 30},
    "03": {"name": "Forge", "interval": 30},
    "04": {"name": "Hammer", "interval": 30},
    "05": {"name": "Aegis", "interval": 30},
    "06": {"name": "Pipeline", "interval": 30},
    "07": {"name": "Launcher", "interval": 30},
    "08": {"name": "Canvas", "interval": 30},
    "09": {"name": "Scribe", "interval": 30},
    "10": {"name": "Tracer", "interval": 30},
    "11": {"name": "Turbo", "interval": 30},
    "12": {"name": "Bridge", "interval": 30},
    "13": {"name": "Maestro", "interval": 30},
    "14": {"name": "Packager", "interval": 30},
    "15": {"name": "Inspector", "interval": 30},
    "16": {"name": "Watchdog", "interval": 30},
}

# Escalation thresholds
WARNING_THRESHOLD = 1    # 1 missed heartbeat = warning
FLAG_THRESHOLD = 2       # 2 missed heartbeats = flag for check
UNRESPONSIVE_THRESHOLD = 3  # 3 missed = considered unresponsive

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_agent_heartbeat_file(agent_id):
    """Get the heartbeat file path for an agent"""
    return HEARTBEAT_DIR / f"{agent_id}.json"

def read_heartbeat(agent_id):
    """Read an agent's heartbeat file"""
    heartbeat_file = get_agent_heartbeat_file(agent_id)
    if not heartbeat_file.exists():
        return None
    
    try:
        with open(heartbeat_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error reading heartbeat for agent {agent_id}: {e}")
        return None

def write_heartbeat(agent_id, data):
    """Write an agent's heartbeat file"""
    heartbeat_file = get_agent_heartbeat_file(agent_id)
    heartbeat_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(heartbeat_file, 'w') as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        logger.error(f"Error writing heartbeat for agent {agent_id}: {e}")

def check_agent_status(agent_id):
    """Check the status of an agent based on heartbeat"""
    agent_info = AGENTS_CONFIG.get(agent_id)
    if not agent_info:
        logger.warning(f"Unknown agent ID: {agent_id}")
        return "unknown"
    
    heartbeat_data = read_heartbeat(agent_id)
    if not heartbeat_data:
        return "missing"
    
    # Parse timestamp
    try:
        last_heartbeat = datetime.fromisoformat(heartbeat_data["timestamp"])
    except (KeyError, ValueError):
        logger.error(f"Invalid timestamp in heartbeat for agent {agent_id}")
        return "error"
    
    # Calculate time since last heartbeat
    time_since = datetime.now() - last_heartbeat
    expected_interval = timedelta(seconds=agent_info["interval"])
    
    # Count missed heartbeats (simplified - in practice would track consecutive misses)
    missed_count = int(time_since.total_seconds() // agent_info["interval"])
    
    if missed_count >= UNRESPONSIVE_THRESHOLD:
        return "unresponsive"
    elif missed_count >= FLAG_THRESHOLD:
        return "flagged"
    elif missed_count >= WARNING_THRESHOLD:
        return "warning"
    else:
        return "healthy"

def monitor_heartbeats():
    """Main monitoring loop"""
    logger.info("Starting heartbeat monitor...")
    
    while True:
        try:
            for agent_id, agent_info in AGENTS_CONFIG.items():
                status = check_agent_status(agent_id)
                
                if status == "healthy":
                    logger.debug(f"Agent {agent_id} ({agent_info['name']}): Healthy")
                elif status == "warning":
                    logger.warning(f"Agent {agent_id} ({agent_info['name']}): Warning - missed heartbeat")
                elif status == "flagged":
                    logger.warning(f"Agent {agent_id} ({agent_info['name']}): Flagged - check recommended")
                elif status == "unresponsive":
                    logger.error(f"Agent {agent_id} ({agent_info['name']}): UNRESPONSIVE - requiring attention")
                    # In a full implementation, this would trigger alerts/notifications
                elif status == "missing":
                    logger.error(f"Agent {agent_id} ({agent_info['name']}): No heartbeat file found")
                elif status == "error":
                    logger.error(f"Agent {agent_id} ({agent_info['name']}): Error reading heartbeat")
                else:
                    logger.info(f"Agent {agent_id} ({agent_info['name']}): {status}")
            
            # Sleep for a short interval before checking again
            time.sleep(10)
            
        except KeyboardInterrupt:
            logger.info("Heartbeat monitor stopped by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error in heartbeat monitor: {e}")
            time.sleep(10)

if __name__ == "__main__":
    monitor_heartbeats()