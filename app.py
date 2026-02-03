import streamlit as st
from access_control import USER_TAG_ACCESS
from n8n_client import get_workflows, get_executions, toggle_workflow
from mock_data import MOCK_WORKFLOWS, MOCK_EXECUTIONS
from datetime import datetime

st.set_page_config(page_title="n8n Kelly Dashboard Demo", layout="wide", page_icon="🤖")

# --- LOGIN ---
st.sidebar.title("Login")
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    if st.sidebar.button("Login"):
        secret_user = st.secrets["users"]["kelly_user"]
        secret_pass = st.secrets["users"]["kelly_pass"]
        if username == secret_user and password == secret_pass:
            st.session_state.logged_in = True
            st.success("Logged in successfully!")
        else:
            st.error("Invalid username or password.")
    st.stop()

allowed_tags = USER_TAG_ACCESS.get(username, [])
if not allowed_tags:
    st.error("You do not have access to any workflows.")
    st.stop()

# --- Fetch workflows ---
all_workflows = MOCK_WORKFLOWS  # using mock workflows
user_workflows = [wf for wf in all_workflows if any(tag in allowed_tags for tag in wf.get("tags", []))]

if not user_workflows:
    st.info("No workflows found for your tags.")
    st.stop()

# --- Sidebar: workflows grouped by tags ---
st.sidebar.title("Workflows")
tag_dict = {}
for wf in user_workflows:
    for tag in wf.get("tags", []):
        if tag in allowed_tags:
            tag_dict.setdefault(tag, []).append(wf)

selected_workflow = None
for tag, workflows in tag_dict.items():
    with st.sidebar.expander(f"{tag.title()} ({len(workflows)})", expanded=True):
        wf_name = st.radio("Select workflow", options=[wf['name'] for wf in workflows], key=f"{tag}_workflow")
        if wf_name:
            selected_workflow = next(wf for wf in workflows if wf['name'] == wf_name)

# --- Main Dashboard ---
if selected_workflow:
    st.header(f"Workflow: {selected_workflow['name']}")
    st.subheader(f"Tags: {', '.join(selected_workflow.get('tags', []))}")
    st.markdown(f"**ID:** `{selected_workflow['id']}`")
    st.markdown(f"**Active:** {'✅ Active' if selected_workflow.get('active') else '❌ Inactive'}")

    # --- Toggle Active / Inactive ---
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Activate Workflow"):
            toggle_workflow(selected_workflow['id'], True)
            st.success("Workflow activated!")
    with col2:
        if st.button("Deactivate Workflow"):
            toggle_workflow(selected_workflow['id'], False)
            st.warning("Workflow deactivated!")

    # --- Recent Executions ---
    st.subheader("Recent Executions")
    executions = MOCK_EXECUTIONS.get(selected_workflow['id'], [])
    if executions:
        for exe in executions:
            status_color = "green" if exe['status']=="success" else "red" if exe['status']=="failed" else "orange"
            start_time = exe['startedAt']
            end_time = exe.get('finishedAt', 'Running')
            with st.expander(f"Execution {exe['id']} - Status: {exe['status'].upper()}"):
                st.markdown(f"- **Started:** {start_time}")
                st.markdown(f"- **Finished:** {end_time}")
                st.json(exe.get('data', {}))
    else:
        st.info("No executions found.")

    # --- Workflow Nodes ---
    st.subheader("Workflow Nodes")
    for node in selected_workflow.get("nodes", []):
        with st.expander(f"{node['name']} ({node['type']})"):
            st.json(node)

st.sidebar.markdown("---")
st.sidebar.markdown(f"Logged in as: **{username}**")