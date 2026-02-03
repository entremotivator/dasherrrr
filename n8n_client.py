import requests
import os
from datetime import datetime
from typing import List, Dict, Optional

# Configuration for n8n API
N8N_API_URL = os.getenv("N8N_API_URL", "http://localhost:5678/api/v1")
N8N_API_KEY = os.getenv("N8N_API_KEY", "")

def get_headers():
    """Return headers for n8n API authentication."""
    return {
        "X-N8N-API-KEY": N8N_API_KEY,
        "Content-Type": "application/json"
    }

def is_api_configured() -> bool:
    """Check if API credentials are configured."""
    return bool(N8N_API_KEY and N8N_API_URL)

def get_workflows() -> List[Dict]:
    """Fetch all workflows from n8n API.
    
    Returns:
        List of workflow dictionaries with id, name, active status, tags, nodes, etc.
    """
    if not is_api_configured():
        return []
    
    try:
        response = requests.get(f"{N8N_API_URL}/workflows", headers=get_headers(), timeout=10)
        response.raise_for_status()
        workflows = response.json().get("data", [])
        
        # Ensure each workflow has required fields
        for wf in workflows:
            if 'tags' not in wf:
                wf['tags'] = []
            if 'nodes' not in wf:
                wf['nodes'] = []
            if 'active' not in wf:
                wf['active'] = False
                
        return workflows
    except requests.exceptions.Timeout:
        print(f"Timeout connecting to n8n API at {N8N_API_URL}")
        return []
    except requests.exceptions.ConnectionError:
        print(f"Connection error: Unable to reach n8n API at {N8N_API_URL}")
        return []
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error fetching workflows: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error fetching workflows: {e}")
        return []

def get_workflow_by_id(workflow_id: str) -> Optional[Dict]:
    """Fetch a specific workflow by ID.
    
    Args:
        workflow_id: The workflow ID to fetch
        
    Returns:
        Workflow dictionary or None if not found
    """
    if not is_api_configured():
        return None
    
    try:
        response = requests.get(
            f"{N8N_API_URL}/workflows/{workflow_id}", 
            headers=get_headers(), 
            timeout=10
        )
        response.raise_for_status()
        return response.json().get("data", None)
    except Exception as e:
        print(f"Error fetching workflow {workflow_id}: {e}")
        return None

def get_executions(workflow_id: str, limit: int = 20, status: str = None) -> List[Dict]:
    """Fetch recent executions for a specific workflow.
    
    Args:
        workflow_id: The workflow ID
        limit: Maximum number of executions to fetch
        status: Filter by status (success, error, waiting, etc.)
        
    Returns:
        List of execution dictionaries
    """
    if not is_api_configured():
        return []
    
    try:
        params = {"workflowId": workflow_id, "limit": limit}
        if status:
            params["status"] = status
            
        response = requests.get(
            f"{N8N_API_URL}/executions", 
            headers=get_headers(), 
            params=params,
            timeout=10
        )
        response.raise_for_status()
        executions = response.json().get("data", [])
        
        # Ensure datetime fields are present
        for exe in executions:
            if 'startedAt' not in exe:
                exe['startedAt'] = datetime.now().isoformat()
            if 'finishedAt' not in exe and exe.get('status') in ['success', 'error']:
                exe['finishedAt'] = exe['startedAt']
                
        return executions
    except Exception as e:
        print(f"Error fetching executions for workflow {workflow_id}: {e}")
        return []

def get_execution_by_id(execution_id: str) -> Optional[Dict]:
    """Fetch detailed information about a specific execution.
    
    Args:
        execution_id: The execution ID
        
    Returns:
        Execution dictionary with full details
    """
    if not is_api_configured():
        return None
    
    try:
        response = requests.get(
            f"{N8N_API_URL}/executions/{execution_id}",
            headers=get_headers(),
            timeout=10
        )
        response.raise_for_status()
        return response.json().get("data", None)
    except Exception as e:
        print(f"Error fetching execution {execution_id}: {e}")
        return None

def toggle_workflow(workflow_id: str, active: bool) -> bool:
    """Activate or deactivate a workflow.
    
    Args:
        workflow_id: The workflow ID
        active: True to activate, False to deactivate
        
    Returns:
        True if successful, False otherwise
    """
    if not is_api_configured():
        return False
    
    try:
        # Update workflow active status
        response = requests.patch(
            f"{N8N_API_URL}/workflows/{workflow_id}",
            headers=get_headers(),
            json={"active": active},
            timeout=10
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error toggling workflow {workflow_id}: {e}")
        return False

def trigger_workflow(workflow_id: str, data: Dict = None) -> Optional[str]:
    """Trigger a workflow execution manually.
    
    Args:
        workflow_id: The workflow ID
        data: Optional data to pass to the workflow
        
    Returns:
        Execution ID if successful, None otherwise
    """
    if not is_api_configured():
        return None
    
    try:
        payload = {"workflowId": workflow_id}
        if data:
            payload["data"] = data
            
        response = requests.post(
            f"{N8N_API_URL}/workflows/{workflow_id}/execute",
            headers=get_headers(),
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        return result.get("data", {}).get("executionId")
    except Exception as e:
        print(f"Error triggering workflow {workflow_id}: {e}")
        return None

def get_workflow_statistics(workflow_id: str, days: int = 30) -> Dict:
    """Get execution statistics for a workflow.
    
    Args:
        workflow_id: The workflow ID
        days: Number of days to analyze
        
    Returns:
        Dictionary with success rate, avg duration, error count, etc.
    """
    executions = get_executions(workflow_id, limit=100)
    
    if not executions:
        return {
            "total": 0,
            "success": 0,
            "error": 0,
            "waiting": 0,
            "success_rate": 0,
            "avg_duration": 0
        }
    
    total = len(executions)
    success = len([e for e in executions if e.get('status') == 'success'])
    error = len([e for e in executions if e.get('status') == 'error'])
    waiting = len([e for e in executions if e.get('status') == 'waiting'])
    
    # Calculate average duration for completed executions
    durations = []
    for exe in executions:
        if exe.get('startedAt') and exe.get('finishedAt'):
            try:
                start = datetime.fromisoformat(exe['startedAt'].replace('Z', '+00:00'))
                finish = datetime.fromisoformat(exe['finishedAt'].replace('Z', '+00:00'))
                duration = (finish - start).total_seconds()
                durations.append(duration)
            except:
                continue
    
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    return {
        "total": total,
        "success": success,
        "error": error,
        "waiting": waiting,
        "success_rate": (success / total * 100) if total > 0 else 0,
        "avg_duration": avg_duration
    }

def get_all_tags() -> List[str]:
    """Get all unique tags from all workflows.
    
    Returns:
        List of unique tag names
    """
    workflows = get_workflows()
    tags = set()
    for wf in workflows:
        tags.update(wf.get('tags', []))
    return sorted(list(tags))

def test_connection() -> Dict:
    """Test connection to n8n API.
    
    Returns:
        Dictionary with connection status and details
    """
    if not is_api_configured():
        return {
            "connected": False,
            "message": "API credentials not configured",
            "url": N8N_API_URL
        }
    
    try:
        response = requests.get(f"{N8N_API_URL}/workflows", headers=get_headers(), timeout=5)
        response.raise_for_status()
        
        workflow_count = len(response.json().get("data", []))
        
        return {
            "connected": True,
            "message": f"Successfully connected to n8n",
            "url": N8N_API_URL,
            "workflow_count": workflow_count
        }
    except requests.exceptions.Timeout:
        return {
            "connected": False,
            "message": "Connection timeout",
            "url": N8N_API_URL
        }
    except requests.exceptions.ConnectionError:
        return {
            "connected": False,
            "message": "Cannot reach n8n server",
            "url": N8N_API_URL
        }
    except requests.exceptions.HTTPError as e:
        return {
            "connected": False,
            "message": f"HTTP error: {e.response.status_code}",
            "url": N8N_API_URL
        }
    except Exception as e:
        return {
            "connected": False,
            "message": f"Error: {str(e)}",
            "url": N8N_API_URL
        }

def delete_execution(execution_id: str) -> bool:
    """Delete a specific execution.
    
    Args:
        execution_id: The execution ID to delete
        
    Returns:
        True if successful, False otherwise
    """
    if not is_api_configured():
        return False
    
    try:
        response = requests.delete(
            f"{N8N_API_URL}/executions/{execution_id}",
            headers=get_headers(),
            timeout=10
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error deleting execution {execution_id}: {e}")
        return False

def get_credentials() -> List[Dict]:
    """Fetch all credentials from n8n.
    
    Returns:
        List of credential dictionaries
    """
    if not is_api_configured():
        return []
    
    try:
        response = requests.get(
            f"{N8N_API_URL}/credentials",
            headers=get_headers(),
            timeout=10
        )
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        print(f"Error fetching credentials: {e}")
        return []
