MOCK_WORKFLOWS = [
    {
        "id": "wf1",
        "name": "Kelly Demo Workflow 1",
        "tags": ["Kelly"],
        "active": True,
        "nodes": [
            {"name": "Start", "type": "n8n-nodes-base.start"},
            {"name": "HTTP Request", "type": "n8n-nodes-base.httpRequest"}
        ]
    },
    {
        "id": "wf2",
        "name": "Kelly Demo Workflow 2",
        "tags": ["Kelly"],
        "active": False,
        "nodes": [
            {"name": "Start", "type": "n8n-nodes-base.start"},
            {"name": "Set", "type": "n8n-nodes-base.set"}
        ]
    }
]

MOCK_EXECUTIONS = {
    "wf1": [
        {"id": "exe1", "status": "success", "startedAt": "2026-02-03 10:00:00", "finishedAt": "2026-02-03 10:00:10", "data": {"output":"Hello World"}},
        {"id": "exe2", "status": "failed", "startedAt": "2026-02-03 11:00:00", "finishedAt": "2026-02-03 11:00:05", "data": {"error":"Something went wrong"}}
    ],
    "wf2": [
        {"id": "exe3", "status": "success", "startedAt": "2026-02-03 12:00:00", "finishedAt": "2026-02-03 12:00:08", "data": {"output":"Demo"}}
    ]
}