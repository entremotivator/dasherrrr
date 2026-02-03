import requests
import os

# Configuration for n8n API
N8N_API_URL = os.getenv("N8N_API_URL", "http://localhost:5678/api/v1")
N8N_API_KEY = os.getenv("N8N_API_KEY", "")

def get_headers():
    return {
        "X-N8N-API-KEY": N8N_API_KEY,
        "Content-Type": "application/json"
    }

def get_workflows():
    """Fetch all workflows from n8n."""
    if not N8N_API_KEY:
        from mock_data import MOCK_WORKFLOWS
        return MOCK_WORKFLOWS
    
    try:
        response = requests.get(f"{N8N_API_URL}/workflows", headers=get_headers())
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        print(f"Error fetching workflows: {e}")
        from mock_data import MOCK_WORKFLOWS
        return MOCK_WORKFLOWS

def get_executions(workflow_id, limit=10):
    """Fetch recent executions for a specific workflow."""
    if not N8N_API_KEY:
        from mock_data import MOCK_EXECUTIONS
        return MOCK_EXECUTIONS.get(workflow_id, [])
    
    try:
        params = {"workflowId": workflow_id, "limit": limit}
        response = requests.get(f"{N8N_API_URL}/executions", headers=get_headers(), params=params)
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        print(f"Error fetching executions: {e}")
        from mock_data import MOCK_EXECUTIONS
        return MOCK_EXECUTIONS.get(workflow_id, [])

def toggle_workflow(workflow_id, active):
    """Activate or deactivate a workflow."""
    if not N8N_API_KEY:
        return True
    
    try:
        endpoint = "activate" if active else "deactivate"
        response = requests.post(f"{N8N_API_URL}/workflows/{workflow_id}/{endpoint}", headers=get_headers())
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error toggling workflow: {e}")
        return False

def trigger_workflow(workflow_id):
    """Trigger a workflow manually (if it has a webhook or manual trigger)."""
    # Note: n8n API doesn't have a direct 'trigger' endpoint for all workflows, 
    # usually done via webhook. This is a placeholder for future implementation.
    return False
