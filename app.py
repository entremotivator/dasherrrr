import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from access_control import USER_TAG_ACCESS
from n8n_client import get_workflows, get_executions, toggle_workflow
import time

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="n8n Matrix Terminal",
    page_icon="📟",
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
    st.sidebar.title("⚡ SYSTEM ACCESS")
    with st.sidebar:
        username = st.text_input("USER_ID", placeholder="Enter ID...")
        password = st.text_input("ACCESS_CODE", type="password", placeholder="********")
        
        if st.button("INITIALIZE", use_container_width=True):
            # Admin and Kelly credentials
            valid_users = {
                "kelly": "password",
                "admin": "admin123"
            }
            
            if username in valid_users and password == valid_users[username]:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("ACCESS DENIED: INVALID CREDENTIALS")

if not st.session_state.logged_in:
    login_page()
    st.markdown("<h1 style='text-align: center; margin-top: 20%;'>[ SYSTEM OFFLINE ]</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>PLEASE AUTHENTICATE VIA TERMINAL</p>", unsafe_allow_html=True)
    st.stop()

# --- DATA LOADING & STRICT FILTERING ---
username = st.session_state.username
all_workflows = get_workflows()

# Strict Access Control Logic
if username == "admin":
    # Admin sees everything
    user_workflows = all_workflows
    allowed_tags = list(set([tag for wf in all_workflows for tag in wf.get("tags", [])]))
else:
    # Regular users only see workflows with their assigned tags
    user_allowed_tags = USER_TAG_ACCESS.get(username, [])
    user_workflows = [wf for wf in all_workflows if any(tag in user_allowed_tags for tag in wf.get("tags", []))]
    allowed_tags = user_allowed_tags

if not user_workflows:
    st.error(f"FATAL ERROR: NO WORKFLOWS AUTHORIZED FOR USER [{username.upper()}]")
    if st.sidebar.button("LOGOUT"):
        st.session_state.logged_in = False
        st.rerun()
    st.stop()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title(f"👤 USER: {username.upper()}")
st.sidebar.markdown("---")

# Search and Filter
search_query = st.sidebar.text_input("🔎 SCAN_NAME", "")
selected_tag = st.sidebar.selectbox("🏷️ FILTER_TAG", ["ALL_TAGS"] + allowed_tags)

filtered_workflows = user_workflows
if search_query:
    filtered_workflows = [wf for wf in filtered_workflows if search_query.lower() in wf['name'].lower()]
if selected_tag != "ALL_TAGS":
    filtered_workflows = [wf for wf in filtered_workflows if selected_tag in wf.get("tags", [])]

st.sidebar.subheader(f"NODES_FOUND: {len(filtered_workflows)}")

# Workflow Selection
for wf in filtered_workflows:
    status_prefix = "[ACTIVE]" if wf.get('active') else "[OFFLINE]"
    if st.sidebar.button(f"{status_prefix} {wf['name']}", key=f"btn_{wf['id']}", use_container_width=True):
        st.session_state.selected_wf_id = wf['id']

st.sidebar.markdown("---")
if st.sidebar.button("TERMINATE_SESSION", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

# --- MAIN CONTENT ---
if not st.session_state.selected_wf_id and filtered_workflows:
    st.session_state.selected_wf_id = filtered_workflows[0]['id']

selected_wf = next((wf for wf in user_workflows if wf['id'] == st.session_state.selected_wf_id), None)

if selected_wf:
    # Header Section
    st.title(f"> WORKFLOW: {selected_wf['name']}")
    st.markdown(f"**ID:** `{selected_wf['id']}` | **TAGS:** {', '.join(selected_wf.get('tags', []))}")
    
    # Action Buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⚡ EXECUTE_NOW", use_container_width=True):
            st.toast("TRANSMITTING SIGNAL...")
            time.sleep(0.5)
            st.success("EXECUTION SIGNAL SENT")
    with col2:
        is_active = selected_wf.get('active', False)
        if is_active:
            if st.button("🛑 DEACTIVATE", use_container_width=True):
                if toggle_workflow(selected_wf['id'], False):
                    st.rerun()
        else:
            if st.button("🟢 ACTIVATE", use_container_width=True):
                if toggle_workflow(selected_wf['id'], True):
                    st.rerun()
    with col3:
        if st.button("🔄 REFRESH_STREAM", use_container_width=True):
            st.rerun()

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["[ DATA_OVERVIEW ]", "[ EXECUTION_LOGS ]", "[ NODE_MAP ]"])

    with tab1:
        executions = get_executions(selected_wf['id'])
        total = len(executions)
        success = len([e for e in executions if e['status'] == 'success'])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("TOTAL_RUNS", total)
        m2.metric("SUCCESS_RUNS", success)
        m3.metric("EFFICIENCY", f"{(success/total*100 if total > 0 else 0):.1f}%")

        if executions:
            df = pd.DataFrame(executions)
            df['startedAt'] = pd.to_datetime(df['startedAt'])
            fig = px.line(df, x='startedAt', y=df.index, title="TEMPORAL_FLOW")
            fig.update_layout(
                plot_bgcolor='black',
                paper_bgcolor='black',
                font_color='#00FF41',
                xaxis=dict(gridcolor='#003300'),
                yaxis=dict(gridcolor='#003300')
            )
            fig.update_traces(line_color='#00FF41')
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        if executions:
            for exe in executions:
                with st.expander(f"LOG_ID: {exe['id']} | STATUS: {exe['status'].upper()}"):
                    st.text(f"START_TIME: {exe['startedAt']}")
                    st.json(exe.get('data', {}))
        else:
            st.info("NO LOGS FOUND IN BUFFER")

    with tab3:
        for node in selected_wf.get('nodes', []):
            with st.expander(f"NODE: {node['name']}"):
                st.code(f"TYPE: {node['type']}", language="bash")

else:
    st.title("> SYSTEM_READY")
    st.info("AWAITING NODE SELECTION...")

# --- FOOTER ---
st.sidebar.markdown("---")
st.sidebar.caption("MATRIX_OS v3.0.1")
