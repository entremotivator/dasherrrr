from datetime import datetime, timedelta

def get_past_time(minutes_ago):
    return (datetime.now() - timedelta(minutes=minutes_ago)).strftime("%Y-%m-%d %H:%M:%S")

MOCK_WORKFLOWS = [
    {
        "id": "wf1",
        "name": "Kelly's Personal Assistant",
        "tags": ["Kelly"],
        "active": True,
        "nodes": [
            {"name": "Voice Trigger", "type": "n8n-nodes-base.webhook"},
            {"name": "AI Agent", "type": "n8n-nodes-base.openAi"}
        ],
        "updatedAt": get_past_time(10)
    },
    {
        "id": "wf2",
        "name": "Kelly's Data Sync",
        "tags": ["Kelly"],
        "active": True,
        "nodes": [
            {"name": "Cron", "type": "n8n-nodes-base.cron"},
            {"name": "Google Sheets", "type": "n8n-nodes-base.googleSheets"}
        ],
        "updatedAt": get_past_time(60)
    },
    {
        "id": "wf3",
        "name": "Corporate Finance Bot",
        "tags": ["Finance"],
        "active": True,
        "nodes": [
            {"name": "Webhook", "type": "n8n-nodes-base.webhook"},
            {"name": "Stripe", "type": "n8n-nodes-base.stripe"}
        ],
        "updatedAt": get_past_time(30)
    },
    {
        "id": "wf4",
        "name": "DevOps Alert System",
        "tags": ["DevOps"],
        "active": False,
        "nodes": [
            {"name": "Error Trigger", "type": "n8n-nodes-base.errorTrigger"}
        ],
        "updatedAt": get_past_time(120)
    }
]

MOCK_EXECUTIONS = {
    "wf1": [
        {"id": "101", "status": "success", "startedAt": get_past_time(5), "finishedAt": get_past_time(4), "data": {"response": "Task completed for Kelly"}},
        {"id": "102", "status": "success", "startedAt": get_past_time(15), "finishedAt": get_past_time(14), "data": {"response": "Meeting scheduled"}}
    ],
    "wf2": [
        {"id": "201", "status": "success", "startedAt": get_past_time(30), "finishedAt": get_past_time(29), "data": {"rows_synced": 45}}
    ]
}
