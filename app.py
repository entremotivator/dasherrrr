import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from access_control import USER_TAG_ACCESS
from n8n_client import get_workflows, get_executions, toggle_workflow
import time

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="n8n Workflow Manager Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .status-badge {
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.8rem;
    }
    .status-active { background-color: #d4edda; color: #155724; }
    .status-inactive { background-color: #f8d7da; color: #721c24; }
    .status-success { background-color: #cce5ff; color: #004085; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "selected_wf_id" not in st.session_state:
    st.session_state.selected_wf_id = None

# --- LOGIN ---
def login_page():
    st.sidebar.title("🔐 Authentication")
    with st.sidebar:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", use_container_width=True):
            # In a real app, use a proper auth system. 
            # For this demo, we'll check against st.secrets or a simple check
            try:
                secret_user = st.secrets["users"]["kelly_user"]
                secret_pass = st.secrets["users"]["kelly_pass"]
            except:
                # Fallback for local testing without secrets
                secret_user, secret_pass = "kelly", "password"
                
            if username == secret_user and password == secret_pass:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid credentials")

if not st.session_state.logged_in:
    login_page()
    st.info("Please login to access your n8n workflows.")
    st.stop()

# --- DATA LOADING ---
username = st.session_state.username
allowed_tags = USER_TAG_ACCESS.get(username, [])

if not allowed_tags:
    st.error("Access Denied: No tags assigned to your account.")
    st.stop()

all_workflows = get_workflows()
user_workflows = [wf for wf in all_workflows if any(tag in allowed_tags for tag in wf.get("tags", []))]

# --- SIDEBAR NAVIGATION ---
st.sidebar.title(f"👋 Welcome, {username.title()}")
st.sidebar.markdown("---")

# Search and Filter
search_query = st.sidebar.text_input("🔍 Search Workflows", "")
selected_tag = st.sidebar.selectbox("🏷️ Filter by Tag", ["All"] + allowed_tags)

filtered_workflows = user_workflows
if search_query:
    filtered_workflows = [wf for wf in filtered_workflows if search_query.lower() in wf['name'].lower()]
if selected_tag != "All":
    filtered_workflows = [wf for wf in filtered_workflows if selected_tag in wf.get("tags", [])]

st.sidebar.subheader(f"Workflows ({len(filtered_workflows)})")

# Workflow Selection
for wf in filtered_workflows:
    status_icon = "🟢" if wf.get('active') else "⚪"
    if st.sidebar.button(f"{status_icon} {wf['name']}", key=f"btn_{wf['id']}", use_container_width=True):
        st.session_state.selected_wf_id = wf['id']

if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

# --- MAIN CONTENT ---
if not st.session_state.selected_wf_id and filtered_workflows:
    st.session_state.selected_wf_id = filtered_workflows[0]['id']

selected_wf = next((wf for wf in user_workflows if wf['id'] == st.session_state.selected_wf_id), None)

if selected_wf:
    # Header Section
    col_title, col_status = st.columns([3, 1])
    with col_title:
        st.title(f"Workflow: {selected_wf['name']}")
        st.caption(f"ID: `{selected_wf['id']}` | Tags: {', '.join(selected_wf.get('tags', []))}")
    
    with col_status:
        is_active = selected_wf.get('active', False)
        st.write("") # spacing
        if is_active:
            st.success("✅ ACTIVE")
        else:
            st.error("❌ INACTIVE")

    # Action Buttons
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("▶️ Trigger Now", use_container_width=True):
            st.toast("Triggering workflow...")
            time.sleep(1)
            st.success("Workflow triggered!")
    with col2:
        if is_active:
            if st.button("⏸️ Deactivate", use_container_width=True):
                if toggle_workflow(selected_wf['id'], False):
                    st.rerun()
        else:
            if st.button("🚀 Activate", use_container_width=True):
                if toggle_workflow(selected_wf['id'], True):
                    st.rerun()
    with col3:
        st.button("🔄 Refresh Data", use_container_width=True)
    with col4:
        st.button("⚙️ Settings", use_container_width=True)

    st.markdown("---")

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "📜 Execution History", "🧩 Node Structure"])

    with tab1:
        # Metrics
        executions = get_executions(selected_wf['id'])
        total_execs = len(executions)
        success_execs = len([e for e in executions if e['status'] == 'success'])
        failed_execs = total_execs - success_execs
        success_rate = (success_execs / total_execs * 100) if total_execs > 0 else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Executions", total_execs)
        m2.metric("Success", success_execs)
        m3.metric("Failed", failed_execs, delta=f"-{failed_execs}" if failed_execs > 0 else "0", delta_color="inverse")
        m4.metric("Success Rate", f"{success_rate:.1f}%")

        # Chart
        if executions:
            df = pd.DataFrame(executions)
            df['startedAt'] = pd.to_datetime(df['startedAt'])
            fig = px.area(df, x='startedAt', y=df.index, title="Execution Timeline", 
                          labels={'index': 'Execution Count', 'startedAt': 'Time'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No execution data available for charts.")

    with tab2:
        st.subheader("Recent Executions")
        if executions:
            for exe in executions:
                status = exe['status'].upper()
                color = "green" if status == "SUCCESS" else "red"
                with st.expander(f"Execution {exe['id']} - {status}", expanded=False):
                    c1, c2 = st.columns(2)
                    c1.markdown(f"**Started:** {exe['startedAt']}")
                    c2.markdown(f"**Finished:** {exe.get('finishedAt', 'N/A')}")
                    st.markdown("**Output Data:**")
                    st.json(exe.get('data', {}))
        else:
            st.info("No executions found for this workflow.")

    with tab3:
        st.subheader("Workflow Nodes")
        nodes = selected_wf.get('nodes', [])
        if nodes:
            for node in nodes:
                with st.expander(f"🔹 {node['name']} ({node['type']})"):
                    st.code(f"Type: {node['type']}\nName: {node['name']}", language="yaml")
        else:
            st.info("No nodes found in this workflow.")

else:
    st.title("n8n Workflow Manager")
    st.info("Select a workflow from the sidebar to view details.")
    
    # Dashboard Overview
    st.subheader("Global Overview")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Accessible Workflows", len(user_workflows))
    with col2:
        active_count = len([wf for wf in user_workflows if wf.get('active')])
        st.metric("Active Workflows", active_count)

# --- FOOTER ---
st.sidebar.markdown("---")
st.sidebar.caption("n8n Manager Pro v2.0")
