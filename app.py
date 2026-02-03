import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from access_control import (
    USER_TAG_ACCESS, get_user_permissions, has_workflow_access,
    can_execute_workflow, can_toggle_workflow, filter_workflows_by_access,
    AuditLogger, get_all_users
)
from n8n_client import (
    get_workflows, get_executions, toggle_workflow, trigger_workflow,
    get_workflow_statistics, test_connection, get_all_tags,
    get_execution_by_id, is_api_configured
)
import time

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="n8n Matrix Terminal",
    page_icon="🔟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MATRIX THEME CSS ---
st.markdown("""
    <style>
    /* Main background and text */
    .stApp {
        background-color: #000000;
        color: #00FF41;
        font-family: 'Courier New', Courier, monospace;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #050505;
        border-right: 1px solid #00FF41;
    }
    [data-testid="stSidebar"] * {
        color: #00FF41 !important;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6, p, span, label {
        color: #00FF41 !important;
        text-shadow: 0 0 5px #00FF41;
    }

    /* Buttons */
    .stButton>button {
        background-color: #000000;
        color: #00FF41;
        border: 1px solid #00FF41;
        border-radius: 0px;
        transition: all 0.3s;
        text-transform: uppercase;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #00FF41;
        color: #000000;
        box-shadow: 0 0 15px #00FF41;
    }

    /* Inputs */
    .stTextInput>div>div>input {
        background-color: #000000;
        color: #00FF41;
        border: 1px solid #00FF41;
    }
    
    /* Selectbox */
    .stSelectbox>div>div>div {
        background-color: #000000;
        color: #00FF41;
        border: 1px solid #00FF41;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #000000 !important;
        border: 1px solid #00FF41 !important;
        color: #00FF41 !important;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #00FF41 !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #000000;
        border: 1px solid #00FF41;
        color: #00FF41;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00FF41 !important;
        color: #000000 !important;
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
    }
    ::-webkit-scrollbar-track {
        background: #000;
    }
    ::-webkit-scrollbar-thumb {
        background: #00FF41;
    }
    
    /* Tables */
    .dataframe {
        color: #00FF41 !important;
        background-color: #000000 !important;
    }
    
    /* Success/Error messages */
    .stSuccess {
        background-color: #001a00 !important;
        color: #00FF41 !important;
        border: 1px solid #00FF41 !important;
    }
    
    .stError {
        background-color: #1a0000 !important;
        color: #FF0041 !important;
        border: 1px solid #FF0041 !important;
    }
    
    .stWarning {
        background-color: #1a1a00 !important;
        color: #FFFF41 !important;
        border: 1px solid #FFFF41 !important;
    }
    
    .stInfo {
        background-color: #00001a !important;
        color: #4141FF !important;
        border: 1px solid #4141FF !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "selected_wf_id" not in st.session_state:
    st.session_state.selected_wf_id = None
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False

# --- AUTHENTICATION CREDENTIALS ---
# In production, use environment variables or secure credential storage
VALID_USERS = {
    "kelly": "password",
    "admin": "admin123",
    "finance": "finance123",
    "devops": "devops123",
    "sales": "sales123",
}

# --- LOGIN PAGE ---
def login_page():
    st.sidebar.title("⚡ SYSTEM ACCESS")
    
    # Connection status indicator
    conn_status = test_connection()
    if conn_status["connected"]:
        st.sidebar.success(f"✓ API CONNECTED")
        st.sidebar.caption(f"Workflows: {conn_status.get('workflow_count', 0)}")
    else:
        st.sidebar.error(f"✗ API OFFLINE")
        st.sidebar.caption(conn_status.get("message", "Unknown error"))
    
    st.sidebar.markdown("---")
    
    with st.sidebar:
        username = st.text_input("USER_ID", placeholder="Enter ID...")
        password = st.text_input("ACCESS_CODE", type="password", placeholder="********")
        
        if st.button("INITIALIZE", use_container_width=True):
            if username in VALID_USERS and password == VALID_USERS[username]:
                st.session_state.logged_in = True
                st.session_state.username = username
                
                # Log login action
                AuditLogger.log_action(
                    username=username,
                    action="login",
                    status="success"
                )
                
                st.rerun()
            else:
                # Log failed login
                AuditLogger.log_action(
                    username=username or "unknown",
                    action="login",
                    status="failed",
                    details={"reason": "invalid_credentials"}
                )
                st.error("ACCESS DENIED: INVALID CREDENTIALS")

# --- MAIN APP LOGIC ---
if not st.session_state.logged_in:
    login_page()
    st.markdown("<h1 style='text-align: center; margin-top: 20%;'>[ SYSTEM OFFLINE ]</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>PLEASE AUTHENTICATE VIA TERMINAL</p>", unsafe_allow_html=True)
    st.stop()

# --- USER CONTEXT ---
username = st.session_state.username
user_perms = get_user_permissions(username)

# --- CHECK API CONNECTION ---
if not is_api_configured():
    st.error("⚠️ N8N API NOT CONFIGURED")
    st.info("Please set N8N_API_URL and N8N_API_KEY environment variables")
    st.code("""
    export N8N_API_URL="http://your-n8n-instance:5678/api/v1"
    export N8N_API_KEY="your-api-key"
    """)
    
    if st.sidebar.button("LOGOUT"):
        st.session_state.logged_in = False
        AuditLogger.log_action(username=username, action="logout", status="success")
        st.rerun()
    st.stop()

# --- DATA LOADING ---
all_workflows = get_workflows()

if not all_workflows:
    st.warning("⚠️ NO WORKFLOWS FOUND - Check n8n connection")
    if st.sidebar.button("LOGOUT"):
        st.session_state.logged_in = False
        AuditLogger.log_action(username=username, action="logout", status="success")
        st.rerun()
    st.stop()

# Filter workflows by user access
user_workflows = filter_workflows_by_access(username, all_workflows)
allowed_tags = user_perms["allowed_tags"] if user_perms["role"] != "administrator" else get_all_tags()

if not user_workflows:
    st.error(f"FATAL ERROR: NO WORKFLOWS AUTHORIZED FOR USER [{username.upper()}]")
    st.info("Contact administrator to request access")
    if st.sidebar.button("LOGOUT"):
        st.session_state.logged_in = False
        AuditLogger.log_action(username=username, action="logout", status="success")
        st.rerun()
    st.stop()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title(f"👤 USER: {username.upper()}")
st.sidebar.caption(f"ROLE: {user_perms['role'].upper()}")
st.sidebar.markdown("---")

# Connection info
conn_status = test_connection()
if conn_status["connected"]:
    st.sidebar.success(f"✓ CONNECTED")
else:
    st.sidebar.error(f"✗ DISCONNECTED")

st.sidebar.markdown("---")

# Search and Filter
search_query = st.sidebar.text_input("🔍 SCAN_NAME", "")
selected_tag = st.sidebar.selectbox("🏷️ FILTER_TAG", ["ALL_TAGS"] + allowed_tags)
status_filter = st.sidebar.selectbox("📊 STATUS", ["ALL", "ACTIVE", "INACTIVE"])

# Apply filters
filtered_workflows = user_workflows.copy()

if search_query:
    filtered_workflows = [wf for wf in filtered_workflows if search_query.lower() in wf['name'].lower()]

if selected_tag != "ALL_TAGS":
    filtered_workflows = [wf for wf in filtered_workflows if selected_tag in wf.get("tags", [])]

if status_filter == "ACTIVE":
    filtered_workflows = [wf for wf in filtered_workflows if wf.get('active')]
elif status_filter == "INACTIVE":
    filtered_workflows = [wf for wf in filtered_workflows if not wf.get('active')]

st.sidebar.subheader(f"NODES_FOUND: {len(filtered_workflows)}")
st.sidebar.markdown("---")

# Workflow Selection
for wf in filtered_workflows:
    status_icon = "🟢" if wf.get('active') else "🔴"
    button_label = f"{status_icon} {wf['name']}"
    
    if st.sidebar.button(button_label, key=f"btn_{wf['id']}", use_container_width=True):
        st.session_state.selected_wf_id = wf['id']
        
        # Log workflow view
        AuditLogger.log_action(
            username=username,
            action="view_workflow",
            workflow_id=wf['id'],
            workflow_name=wf['name'],
            status="success"
        )

# Auto-refresh toggle
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ SETTINGS")
auto_refresh = st.sidebar.checkbox("AUTO-REFRESH (30s)", value=st.session_state.auto_refresh)
st.session_state.auto_refresh = auto_refresh

if st.sidebar.button("TERMINATE_SESSION", use_container_width=True):
    AuditLogger.log_action(username=username, action="logout", status="success")
    st.session_state.logged_in = False
    st.rerun()

# --- MAIN CONTENT ---
if not st.session_state.selected_wf_id and filtered_workflows:
    st.session_state.selected_wf_id = filtered_workflows[0]['id']

selected_wf = next((wf for wf in user_workflows if wf['id'] == st.session_state.selected_wf_id), None)

if selected_wf:
    # Header Section
    col_title, col_refresh = st.columns([4, 1])
    with col_title:
        st.title(f"> WORKFLOW: {selected_wf['name']}")
    with col_refresh:
        if st.button("🔄 REFRESH", use_container_width=True):
            st.rerun()
    
    st.markdown(f"**ID:** `{selected_wf['id']}` | **TAGS:** {', '.join(selected_wf.get('tags', [])) or 'None'}")
    
    # Workflow status badge
    if selected_wf.get('active'):
        st.success("✓ STATUS: ACTIVE")
    else:
        st.warning("⚠ STATUS: INACTIVE")
    
    st.markdown("---")
    
    # Action Buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        can_exec = can_execute_workflow(username, selected_wf.get('tags', []))
        if st.button("⚡ EXECUTE_NOW", use_container_width=True, disabled=not can_exec):
            if can_exec:
                st.toast("TRANSMITTING SIGNAL...")
                execution_id = trigger_workflow(selected_wf['id'])
                
                if execution_id:
                    st.success(f"✓ EXECUTION INITIATED: {execution_id}")
                    AuditLogger.log_action(
                        username=username,
                        action="execute_workflow",
                        workflow_id=selected_wf['id'],
                        workflow_name=selected_wf['name'],
                        status="success",
                        details={"execution_id": execution_id}
                    )
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("✗ EXECUTION FAILED")
                    AuditLogger.log_action(
                        username=username,
                        action="execute_workflow",
                        workflow_id=selected_wf['id'],
                        workflow_name=selected_wf['name'],
                        status="failed"
                    )
    
    with col2:
        can_tog = can_toggle_workflow(username, selected_wf.get('tags', []))
        is_active = selected_wf.get('active', False)
        
        if is_active:
            if st.button("🛑 DEACTIVATE", use_container_width=True, disabled=not can_tog):
                if can_tog and toggle_workflow(selected_wf['id'], False):
                    st.success("✓ WORKFLOW DEACTIVATED")
                    AuditLogger.log_action(
                        username=username,
                        action="deactivate_workflow",
                        workflow_id=selected_wf['id'],
                        workflow_name=selected_wf['name'],
                        status="success"
                    )
                    time.sleep(0.5)
                    st.rerun()
        else:
            if st.button("🟢 ACTIVATE", use_container_width=True, disabled=not can_tog):
                if can_tog and toggle_workflow(selected_wf['id'], True):
                    st.success("✓ WORKFLOW ACTIVATED")
                    AuditLogger.log_action(
                        username=username,
                        action="activate_workflow",
                        workflow_id=selected_wf['id'],
                        workflow_name=selected_wf['name'],
                        status="success"
                    )
                    time.sleep(0.5)
                    st.rerun()
    
    with col3:
        # Get workflow stats
        stats = get_workflow_statistics(selected_wf['id'])
        st.metric("SUCCESS RATE", f"{stats['success_rate']:.1f}%")
    
    with col4:
        st.metric("TOTAL RUNS", stats['total'])

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "[ OVERVIEW ]", 
        "[ EXECUTION_LOGS ]", 
        "[ NODE_MAP ]",
        "[ STATISTICS ]"
    ])

    with tab1:
        # Workflow Overview
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.subheader("⚙️ CONFIGURATION")
            st.write(f"**Workflow ID:** `{selected_wf['id']}`")
            st.write(f"**Name:** {selected_wf['name']}")
            st.write(f"**Active:** {'Yes' if selected_wf.get('active') else 'No'}")
            st.write(f"**Tags:** {', '.join(selected_wf.get('tags', [])) or 'None'}")
            st.write(f"**Node Count:** {len(selected_wf.get('nodes', []))}")
            
            if selected_wf.get('updatedAt'):
                st.write(f"**Last Updated:** {selected_wf['updatedAt']}")
        
        with col_b:
            st.subheader("📊 QUICK STATS")
            
            m1, m2 = st.columns(2)
            m1.metric("Total Executions", stats['total'])
            m2.metric("Success Count", stats['success'])
            
            m3, m4 = st.columns(2)
            m3.metric("Error Count", stats['error'])
            m4.metric("Avg Duration", f"{stats['avg_duration']:.2f}s")

    with tab2:
        # Execution Logs
        st.subheader("📜 EXECUTION HISTORY")
        
        # Execution filter
        exec_status_filter = st.selectbox(
            "Filter by Status",
            ["all", "success", "error", "waiting"],
            key="exec_filter"
        )
        
        executions = get_executions(
            selected_wf['id'], 
            limit=50,
            status=None if exec_status_filter == "all" else exec_status_filter
        )
        
        if executions:
            st.caption(f"Showing {len(executions)} most recent executions")
            
            for exe in executions:
                status = exe.get('status', 'unknown')
                status_icon = "✓" if status == "success" else "✗" if status == "error" else "⏳"
                status_color = "success" if status == "success" else "error" if status == "error" else "info"
                
                with st.expander(f"{status_icon} EXEC_ID: {exe.get('id')} | STATUS: {status.upper()}", expanded=False):
                    col_1, col_2 = st.columns(2)
                    
                    with col_1:
                        st.text(f"Started: {exe.get('startedAt', 'N/A')}")
                        if exe.get('finishedAt'):
                            st.text(f"Finished: {exe['finishedAt']}")
                        
                        # Calculate duration
                        if exe.get('startedAt') and exe.get('finishedAt'):
                            try:
                                start = datetime.fromisoformat(exe['startedAt'].replace('Z', '+00:00'))
                                finish = datetime.fromisoformat(exe['finishedAt'].replace('Z', '+00:00'))
                                duration = (finish - start).total_seconds()
                                st.text(f"Duration: {duration:.2f}s")
                            except:
                                pass
                    
                    with col_2:
                        st.text(f"Status: {status}")
                        if exe.get('mode'):
                            st.text(f"Mode: {exe['mode']}")
                    
                    # Show execution data if available
                    if exe.get('data'):
                        st.subheader("Execution Data")
                        st.json(exe['data'])
        else:
            st.info("NO EXECUTION LOGS FOUND IN BUFFER")

    with tab3:
        # Node Map
        st.subheader("🗺️ WORKFLOW NODES")
        
        nodes = selected_wf.get('nodes', [])
        
        if nodes:
            st.caption(f"Total Nodes: {len(nodes)}")
            
            for idx, node in enumerate(nodes, 1):
                with st.expander(f"NODE {idx}: {node.get('name', 'Unnamed')}", expanded=False):
                    st.code(f"Type: {node.get('type', 'Unknown')}", language="bash")
                    
                    # Show additional node properties if available
                    if node.get('typeVersion'):
                        st.text(f"Version: {node['typeVersion']}")
                    if node.get('position'):
                        st.text(f"Position: {node['position']}")
        else:
            st.info("NO NODE DATA AVAILABLE")

    with tab4:
        # Statistics and Analytics
        st.subheader("📈 WORKFLOW ANALYTICS")
        
        # Get execution data for charts
        recent_executions = get_executions(selected_wf['id'], limit=100)
        
        if recent_executions:
            # Prepare dataframe
            df = pd.DataFrame(recent_executions)
            df['startedAt'] = pd.to_datetime(df['startedAt'])
            df['date'] = df['startedAt'].dt.date
            
            # Executions over time
            daily_counts = df.groupby(['date', 'status']).size().reset_index(name='count')
            
            fig = px.bar(
                daily_counts, 
                x='date', 
                y='count', 
                color='status',
                title="Executions Over Time",
                labels={'date': 'Date', 'count': 'Count', 'status': 'Status'}
            )
            
            fig.update_layout(
                plot_bgcolor='black',
                paper_bgcolor='black',
                font_color='#00FF41',
                xaxis=dict(gridcolor='#003300'),
                yaxis=dict(gridcolor='#003300')
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Status distribution
            status_counts = df['status'].value_counts()
            
            fig2 = go.Figure(data=[go.Pie(
                labels=status_counts.index,
                values=status_counts.values,
                hole=.3
            )])
            
            fig2.update_layout(
                title="Execution Status Distribution",
                plot_bgcolor='black',
                paper_bgcolor='black',
                font_color='#00FF41'
            )
            
            st.plotly_chart(fig2, use_container_width=True)
            
            # Recent performance metrics
            col1, col2, col3 = st.columns(3)
            
            recent_7d = df[df['startedAt'] > (datetime.now() - timedelta(days=7))]
            
            col1.metric("Last 7 Days", len(recent_7d))
            col2.metric("Success Rate", f"{(len(recent_7d[recent_7d['status']=='success'])/len(recent_7d)*100):.1f}%" if len(recent_7d) > 0 else "N/A")
            col3.metric("Error Count", len(recent_7d[recent_7d['status']=='error']))
            
        else:
            st.info("NO EXECUTION DATA FOR ANALYTICS")

else:
    st.title("> SYSTEM_READY")
    st.info("AWAITING NODE SELECTION...")

# --- ADMIN PANEL (if admin user) ---
if user_perms["role"] == "administrator":
    st.sidebar.markdown("---")
    if st.sidebar.button("👁️ ADMIN_PANEL", use_container_width=True):
        st.session_state.show_admin = not st.session_state.get("show_admin", False)
    
    if st.session_state.get("show_admin", False):
        st.markdown("---")
        st.title("🔐 ADMINISTRATOR PANEL")
        
        admin_tab1, admin_tab2, admin_tab3 = st.tabs([
            "[ USER_MANAGEMENT ]",
            "[ AUDIT_LOGS ]",
            "[ SYSTEM_STATUS ]"
        ])
        
        with admin_tab1:
            st.subheader("👥 USER ACCESS CONTROL")
            
            all_users = get_all_users()
            
            for user in all_users:
                with st.expander(f"USER: {user['username'].upper()} - {user['role'].upper()}"):
                    st.write(f"**Role:** {user['role']}")
                    st.write(f"**Allowed Tags:** {', '.join(user['allowed_tags'])}")
                    st.write("**Capabilities:**")
                    for cap, val in user['capabilities'].items():
                        st.write(f"  - {cap}: {'✓' if val else '✗'}")
        
        with admin_tab2:
            st.subheader("📋 AUDIT LOG VIEWER")
            
            # Log filters
            log_user = st.selectbox("Filter by User", ["ALL"] + list(VALID_USERS.keys()))
            log_action = st.selectbox("Filter by Action", ["ALL", "login", "logout", "view_workflow", "execute_workflow", "activate_workflow", "deactivate_workflow"])
            
            # Get logs
            logs = AuditLogger.get_logs(
                username=None if log_user == "ALL" else log_user,
                limit=100,
                action=None if log_action == "ALL" else log_action
            )
            
            if logs:
                st.caption(f"Showing {len(logs)} log entries")
                
                # Convert to dataframe for display
                log_df = pd.DataFrame(logs)
                st.dataframe(log_df, use_container_width=True)
            else:
                st.info("NO AUDIT LOGS FOUND")
        
        with admin_tab3:
            st.subheader("🖥️ SYSTEM STATUS")
            
            conn = test_connection()
            
            if conn["connected"]:
                st.success(f"✓ n8n API Connected")
                st.write(f"**URL:** {conn['url']}")
                st.write(f"**Workflow Count:** {conn.get('workflow_count', 0)}")
            else:
                st.error(f"✗ n8n API Disconnected")
                st.write(f"**URL:** {conn['url']}")
                st.write(f"**Error:** {conn.get('message', 'Unknown')}")
            
            st.markdown("---")
            
            # System metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Workflows", len(all_workflows))
            col2.metric("Total Users", len(all_users))
            col3.metric("Active Workflows", len([w for w in all_workflows if w.get('active')]))

# Auto-refresh logic
if st.session_state.auto_refresh:
    time.sleep(30)
    st.rerun()

# --- FOOTER ---
st.sidebar.markdown("---")
st.sidebar.caption("MATRIX_OS v4.0.0")
st.sidebar.caption(f"Session: {datetime.now().strftime('%H:%M:%S')}")
