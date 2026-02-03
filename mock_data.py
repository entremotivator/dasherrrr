from datetime import datetime, timedelta

def get_past_time(minutes_ago):
    return (datetime.now() - timedelta(minutes=minutes_ago)).strftime("%Y-%m-%d %H:%M:%S")

MOCK_WORKFLOWS = [
    {
        "id": "wf1",
        "name": "Customer Onboarding Sync",
        "tags": ["Kelly", "Sales"],
        "active": True,
        "nodes": [
            {"name": "Onboarding Webhook", "type": "n8n-nodes-base.webhook"},
            {"name": "Filter Data", "type": "n8n-nodes-base.filter"},
            {"name": "Update CRM", "type": "n8n-nodes-base.httpRequest"}
        ],
        "updatedAt": get_past_time(120)
    },
    {
        "id": "wf2",
        "name": "Daily Revenue Report",
        "tags": ["Kelly", "Finance"],
        "active": False,
        "nodes": [
            {"name": "Schedule Trigger", "type": "n8n-nodes-base.cron"},
            {"name": "Query DB", "type": "n8n-nodes-base.mySql"},
            {"name": "Send Email", "type": "n8n-nodes-base.emailSend"}
        ],
        "updatedAt": get_past_time(1440)
    },
    {
        "id": "wf3",
        "name": "Error Notification Bot",
        "tags": ["DevOps"],
        "active": True,
        "nodes": [
            {"name": "Error Trigger", "type": "n8n-nodes-base.errorTrigger"},
            {"name": "Slack Notify", "type": "n8n-nodes-base.slack"}
        ],
        "updatedAt": get_past_time(30)
    }
]

MOCK_EXECUTIONS = {
    "wf1": [
        {"id": "101", "status": "success", "startedAt": get_past_time(10), "finishedAt": get_past_time(9), "data": {"customer": "Acme Corp", "status": "synced"}},
        {"id": "102", "status": "success", "startedAt": get_past_time(60), "finishedAt": get_past_time(59), "data": {"customer": "Globex", "status": "synced"}},
        {"id": "103", "status": "failed", "startedAt": get_past_time(120), "finishedAt": get_past_time(119), "data": {"error": "Timeout connecting to CRM"}}
    ],
    "wf2": [
        {"id": "201", "status": "success", "startedAt": get_past_time(1440), "finishedAt": get_past_time(1439), "data": {"report_sent": True, "revenue": 5000}}
    ],
    "wf3": [
        {"id": "301", "status": "success", "startedAt": get_past_time(5), "finishedAt": get_past_time(4), "data": {"alert": "High CPU usage", "channel": "#alerts"}}
    ]
}
