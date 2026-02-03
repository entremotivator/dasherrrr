from datetime import datetime
from typing import List, Dict, Optional
import json
import os

# Strict access control mapping users to specific tags
USER_TAG_ACCESS = {
    "kelly": ["Kelly"],
    "admin": ["Kelly", "Sales", "Finance", "DevOps", "Marketing", "Support"],
    "finance": ["Finance"],
    "devops": ["DevOps"],
    "sales": ["Sales"],
}

# User roles with different permission levels
USER_ROLES = {
    "admin": "administrator",
    "kelly": "user",
    "finance": "user",
    "devops": "user",
    "sales": "user",
}

# Audit log storage path
AUDIT_LOG_PATH = os.getenv("AUDIT_LOG_PATH", "/tmp/n8n_audit_logs.jsonl")

class AuditLogger:
    """Audit logging for all user actions."""
    
    @staticmethod
    def log_action(username: str, action: str, workflow_id: str = None, 
                   workflow_name: str = None, details: Dict = None, 
                   status: str = "success") -> None:
        """Log a user action to the audit log.
        
        Args:
            username: Username performing the action
            action: Type of action (view, execute, toggle, etc.)
            workflow_id: ID of workflow affected
            workflow_name: Name of workflow affected
            details: Additional details about the action
            status: Status of the action (success, failed, denied)
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "action": action,
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "status": status,
            "details": details or {}
        }
        
        try:
            with open(AUDIT_LOG_PATH, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"Error writing audit log: {e}")
    
    @staticmethod
    def get_logs(username: str = None, limit: int = 100, 
                 action: str = None) -> List[Dict]:
        """Retrieve audit logs.
        
        Args:
            username: Filter by specific username
            limit: Maximum number of logs to return
            action: Filter by action type
            
        Returns:
            List of log entries
        """
        if not os.path.exists(AUDIT_LOG_PATH):
            return []
        
        logs = []
        try:
            with open(AUDIT_LOG_PATH, 'r') as f:
                for line in f:
                    try:
                        log = json.loads(line.strip())
                        
                        # Apply filters
                        if username and log.get('username') != username:
                            continue
                        if action and log.get('action') != action:
                            continue
                        
                        logs.append(log)
                    except json.JSONDecodeError:
                        continue
            
            # Return most recent logs first
            logs.reverse()
            return logs[:limit]
        except Exception as e:
            print(f"Error reading audit logs: {e}")
            return []
    
    @staticmethod
    def get_user_activity_summary(username: str, days: int = 7) -> Dict:
        """Get summary of user activity.
        
        Args:
            username: Username to analyze
            days: Number of days to analyze
            
        Returns:
            Dictionary with activity statistics
        """
        from datetime import timedelta
        
        logs = AuditLogger.get_logs(username=username, limit=1000)
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_logs = [
            log for log in logs 
            if datetime.fromisoformat(log['timestamp']) > cutoff_date
        ]
        
        actions = {}
        workflows_accessed = set()
        
        for log in recent_logs:
            action = log.get('action', 'unknown')
            actions[action] = actions.get(action, 0) + 1
            
            if log.get('workflow_id'):
                workflows_accessed.add(log['workflow_id'])
        
        return {
            "total_actions": len(recent_logs),
            "actions_breakdown": actions,
            "workflows_accessed": len(workflows_accessed),
            "period_days": days
        }
    
    @staticmethod
    def clear_old_logs(days: int = 90) -> int:
        """Clear logs older than specified days.
        
        Args:
            days: Keep logs from this many days
            
        Returns:
            Number of logs deleted
        """
        from datetime import timedelta
        
        if not os.path.exists(AUDIT_LOG_PATH):
            return 0
        
        cutoff_date = datetime.now() - timedelta(days=days)
        kept_logs = []
        deleted_count = 0
        
        try:
            with open(AUDIT_LOG_PATH, 'r') as f:
                for line in f:
                    try:
                        log = json.loads(line.strip())
                        log_date = datetime.fromisoformat(log['timestamp'])
                        
                        if log_date > cutoff_date:
                            kept_logs.append(line)
                        else:
                            deleted_count += 1
                    except:
                        continue
            
            # Rewrite file with kept logs
            with open(AUDIT_LOG_PATH, 'w') as f:
                for line in kept_logs:
                    f.write(line)
            
            return deleted_count
        except Exception as e:
            print(f"Error clearing old logs: {e}")
            return 0

def get_user_permissions(username: str) -> Dict:
    """Get all permissions for a user.
    
    Args:
        username: Username to check
        
    Returns:
        Dictionary with role, tags, and capabilities
    """
    role = USER_ROLES.get(username, "guest")
    tags = USER_TAG_ACCESS.get(username, [])
    
    capabilities = {
        "can_view": len(tags) > 0,
        "can_execute": role in ["administrator", "user"],
        "can_toggle": role == "administrator",
        "can_delete": role == "administrator",
        "can_view_all": role == "administrator",
        "can_view_audit_logs": role == "administrator",
    }
    
    return {
        "username": username,
        "role": role,
        "allowed_tags": tags,
        "capabilities": capabilities
    }

def has_workflow_access(username: str, workflow_tags: List[str]) -> bool:
    """Check if user has access to a workflow based on tags.
    
    Args:
        username: Username to check
        workflow_tags: Tags assigned to the workflow
        
    Returns:
        True if user has access, False otherwise
    """
    if USER_ROLES.get(username) == "administrator":
        return True
    
    user_tags = USER_TAG_ACCESS.get(username, [])
    return any(tag in user_tags for tag in workflow_tags)

def can_execute_workflow(username: str, workflow_tags: List[str]) -> bool:
    """Check if user can execute a workflow.
    
    Args:
        username: Username to check
        workflow_tags: Tags assigned to the workflow
        
    Returns:
        True if user can execute, False otherwise
    """
    permissions = get_user_permissions(username)
    return (
        permissions["capabilities"]["can_execute"] and 
        has_workflow_access(username, workflow_tags)
    )

def can_toggle_workflow(username: str, workflow_tags: List[str]) -> bool:
    """Check if user can toggle (activate/deactivate) a workflow.
    
    Args:
        username: Username to check
        workflow_tags: Tags assigned to the workflow
        
    Returns:
        True if user can toggle, False otherwise
    """
    permissions = get_user_permissions(username)
    return (
        permissions["capabilities"]["can_toggle"] and 
        has_workflow_access(username, workflow_tags)
    )

def filter_workflows_by_access(username: str, workflows: List[Dict]) -> List[Dict]:
    """Filter workflows based on user access.
    
    Args:
        username: Username to filter for
        workflows: List of all workflows
        
    Returns:
        Filtered list of workflows user can access
    """
    if USER_ROLES.get(username) == "administrator":
        return workflows
    
    user_tags = USER_TAG_ACCESS.get(username, [])
    return [
        wf for wf in workflows 
        if any(tag in user_tags for tag in wf.get("tags", []))
    ]

def add_user_access(username: str, tags: List[str], role: str = "user") -> bool:
    """Add or update user access (admin only operation).
    
    Args:
        username: Username to add/update
        tags: Tags the user should have access to
        role: Role to assign
        
    Returns:
        True if successful
    """
    USER_TAG_ACCESS[username] = tags
    USER_ROLES[username] = role
    return True

def remove_user_access(username: str) -> bool:
    """Remove user access (admin only operation).
    
    Args:
        username: Username to remove
        
    Returns:
        True if successful
    """
    if username in USER_TAG_ACCESS:
        del USER_TAG_ACCESS[username]
    if username in USER_ROLES:
        del USER_ROLES[username]
    return True

def get_all_users() -> List[Dict]:
    """Get list of all users and their permissions.
    
    Returns:
        List of user permission dictionaries
    """
    users = []
    for username in USER_TAG_ACCESS.keys():
        users.append(get_user_permissions(username))
    return users
