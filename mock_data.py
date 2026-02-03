from datetime import datetime, timedelta
import random

def get_past_time(minutes_ago):
    return (datetime.now() - timedelta(minutes=minutes_ago)).strftime("%Y-%m-%d %H:%M:%S")

# Expanded Workflows
MOCK_WORKFLOWS = [
    {"id": "wf1", "name": "Kelly's Neural Link", "tags": ["Kelly", "AI"], "active": True, "updatedAt": get_past_time(5), "nodes": [{"name": "Input", "type": "webhook"}, {"name": "Process", "type": "openAi"}]},
    {"id": "wf2", "name": "Kelly's Data Stream", "tags": ["Kelly", "Database"], "active": True, "updatedAt": get_past_time(45), "nodes": [{"name": "Cron", "type": "cron"}, {"name": "Sync", "type": "postgres"}]},
    {"id": "wf3", "name": "Zion Mainframe Sync", "tags": ["Zion", "Security"], "active": True, "updatedAt": get_past_time(120), "nodes": [{"name": "Auth", "type": "webhook"}, {"name": "Verify", "type": "crypto"}]},
    {"id": "wf4", "name": "Nebuchadnezzar Comms", "tags": ["Nebuchadnezzar", "Comms"], "active": False, "updatedAt": get_past_time(300), "nodes": [{"name": "Signal", "type": "slack"}]},
    {"id": "wf5", "name": "Agent Smith Detector", "tags": ["Security", "Admin"], "active": True, "updatedAt": get_past_time(10), "nodes": [{"name": "Scan", "type": "http"}]},
    {"id": "wf6", "name": "Oracle's Prediction", "tags": ["Kelly", "Oracle"], "active": True, "updatedAt": get_past_time(15), "nodes": [{"name": "Query", "type": "openAi"}]}
]

# Generate random executions for more data
MOCK_EXECUTIONS = {}
for wf in MOCK_WORKFLOWS:
    execs = []
    for i in range(15):
        status = "success" if random.random() > 0.2 else "failed"
        execs.append({
            "id": f"exe_{wf['id']}_{i}",
            "status": status,
            "startedAt": get_past_time(random.randint(1, 1440)),
            "finishedAt": get_past_time(0),
            "data": {"payload": f"Data packet {i}", "latency": f"{random.randint(100, 500)}ms"}
        })
    MOCK_EXECUTIONS[wf['id']] = execs

# Audit Logs
MOCK_AUDIT_LOGS = [
    {"timestamp": get_past_time(2), "user": "admin", "action": "ACCESS_GRANTED", "target": "SYSTEM_CORE"},
    {"timestamp": get_past_time(10), "user": "kelly", "action": "WORKFLOW_TRIGGER", "target": "wf1"},
    {"timestamp": get_past_time(25), "user": "admin", "action": "TAG_MODIFIED", "target": "wf3"},
    {"timestamp": get_past_time(60), "user": "kelly", "action": "LOGIN", "target": "TERMINAL_01"}
]
