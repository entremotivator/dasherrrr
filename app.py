import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import random
from n8n_client import get_workflows, get_executions, toggle_workflow
from mock_data import MOCK_AUDIT_LOGS

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="MATRIX_OS // N8N_CONTROL",
    page_icon="📟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ADVANCED MATRIX THEME CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');

    * {
        font-family: 'Share Tech Mono', monospace !important;
    }

    .stApp {
        background-color: #000000;
        background-image: linear-gradient(rgba(0, 255, 65, 0.05) 1px, transparent 1px),
                          linear-gradient(90deg, rgba(0, 255, 65, 0.05) 1px, transparent 1px);
        background-size: 20px 20px;
        color: #00FF41;
    }
    
    .glow {
        text-shadow: 0 0 5px #00FF41, 0 0 10px #00FF41;
    }

    [data-testid="stSidebar"] {
        background-color: #020202;
        border-right: 2px solid #00FF41;
        box-shadow: 5px 0 15px rgba(0, 255, 65, 0.2);
    }

    .terminal-card {
        border: 1px solid #00FF41;
        padding: 20px;
        background: rgba(0, 0, 0, 0.8);
        box-shadow: inset 0 0 10px #00FF41;
        margin-bottom: 20px;
    }

    .stButton>button {
        width: 100%;
        background-color: transparent;
        color: #00FF41;
        border: 1px solid #00FF41;
        border-radius: 0px;
        padding: 10px;
        transition: 0.3s all;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .stButton>button:hover {
        background-color: #00FF41;
        color: #000;
        box-shadow: 0 0 20px #00FF41;
    }

    [data-testid="stMetric"] {
        border: 1px solid #00FF41;
        padding: 10px;
        background: rgba(0, 50, 0, 0.1);
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "selected_wf_id" not in st.session_state:
    st.session_state.selected_wf_id = None
if "view" not in st.session_state:
    st.session_state.view = "DASHBOARD"

# --- AUTHENTICATION USING ST.SECRETS ---
def login_screen():
    st.markdown("<h1 style='text-align: center; font-size: 60px;' class='glow'>MATRIX_OS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; letter-spacing: 5px;'>SYSTEM_AUTHENTICATION_REQUIRED</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            u = st.text_input("USER_IDENTIFIER", placeholder="ID...")
            p = st.text_input("ACCESS_KEY", type="password", placeholder="****")
            if st.form_submit_button("INITIALIZE_SEQUENCE"):
                # Check against st.secrets
                if "users" in st.secrets and u in st.secrets["users"]:
                    if p == st.secrets["users"][u]["password"]:
                        st.session_state.logged_in = True
                        st.session_state.username = u
                        st.rerun()
                    else:
                        st.error("INVALID_ACCESS_KEY // ACCESS_DENIED")
                else:
                    st.error("USER_NOT_FOUND // ACCESS_DENIED")

if not st.session_state.logged_in:
    login_screen()
    st.stop()

# --- DATA PROCESSING & ACCESS CONTROL ---
username = st.session_state.username
all_workflows = get_workflows()

# Get allowed tags from st.secrets for the logged-in user
allowed_tags = st.secrets["users"][username].get("tags", [])

if username == "admin":
    user_workflows = all_workflows
else:
    user_workflows = [wf for wf in all_workflows if any(tag in allowed_tags for tag in wf.get("tags", []))]

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"<h2 class='glow'>USER: {username.upper()}</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    if st.button("📊 GLOBAL_DASHBOARD"): st.session_state.view = "DASHBOARD"
    if st.button("📜 AUDIT_LOGS"): st.session_state.view = "AUDIT"
    if st.button("⚙️ SYSTEM_SETTINGS"): st.session_state.view = "SETTINGS"
    
    st.markdown("---")
    st.subheader("WORKFLOW_NODES")
    search = st.text_input("SCAN_ID", "")
    tag_filter = st.selectbox("TAG_FILTER", ["ALL"] + list(allowed_tags))
    
    filtered = user_workflows
    if search: filtered = [wf for wf in filtered if search.lower() in wf['name'].lower()]
    if tag_filter != "ALL": filtered = [wf for wf in filtered if tag_filter in wf.get("tags", [])]
    
    for wf in filtered:
        label = f"{'[A]' if wf.get('active') else '[O]'} {wf['name']}"
        if st.button(label, key=f"nav_{wf['id']}"):
            st.session_state.selected_wf_id = wf['id']
            st.session_state.view = "WORKFLOW"
            
    st.markdown("---")
    if st.button("❌ TERMINATE"):
        st.session_state.logged_in = False
        st.rerun()

# --- MAIN VIEWS ---
if st.session_state.view == "DASHBOARD":
    st.markdown("<h1 class='glow'>> GLOBAL_SYSTEM_OVERVIEW</h1>", unsafe_allow_html=True)
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("TOTAL_NODES", len(user_workflows))
    m2.metric("ACTIVE_STREAMS", len([wf for wf in user_workflows if wf.get('active')]))
    m3.metric("SYSTEM_HEALTH", "98.4%")
    m4.metric("UPTIME", "1024:12:04")
    
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("### DATA_FLOW_DISTRIBUTION")
        tag_counts = {}
        for wf in user_workflows:
            for tag in wf.get('tags', []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        df_tags = pd.DataFrame(list(tag_counts.items()), columns=['Tag', 'Count'])
        fig = px.pie(df_tags, values='Count', names='Tag', hole=.3)
        fig.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='#00FF41')
        st.plotly_chart(fig, use_container_width=True)
        
    with col_right:
        st.markdown("### RECENT_ACTIVITY_PULSE")
        pulse_data = pd.DataFrame({
            'Time': pd.date_range(start='now', periods=20, freq='min'),
            'Load': [random.randint(20, 90) for _ in range(20)]
        })
        fig = px.line(pulse_data, x='Time', y='Load')
        fig.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='#00FF41')
        fig.update_traces(line_color='#00FF41')
        st.plotly_chart(fig, use_container_width=True)

elif st.session_state.view == "AUDIT":
    st.markdown("<h1 class='glow'>> SYSTEM_AUDIT_LOGS</h1>", unsafe_allow_html=True)
    st.table(pd.DataFrame(MOCK_AUDIT_LOGS))

elif st.session_state.view == "WORKFLOW":
    wf = next((w for w in user_workflows if w['id'] == st.session_state.selected_wf_id), None)
    if wf:
        st.markdown(f"<h1 class='glow'>> NODE: {wf['name'].upper()}</h1>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("⚡ EXECUTE"): st.toast("SIGNAL_SENT")
        with c2:
            if wf['active']:
                if st.button("🛑 DEACTIVATE"): 
                    toggle_workflow(wf['id'], False)
                    st.rerun()
            else:
                if st.button("🚀 ACTIVATE"): 
                    toggle_workflow(wf['id'], True)
                    st.rerun()
        with c3: st.button("🔄 SYNC")
        with c4: st.button("🛠️ CONFIG")
            
        st.markdown("---")
        t1, t2, t3 = st.tabs(["📊 ANALYTICS", "📜 LOGS", "🧩 STRUCTURE"])
        
        with t1:
            execs = get_executions(wf['id'])
            if execs:
                df = pd.DataFrame(execs)
                df['startedAt'] = pd.to_datetime(df['startedAt'])
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    fig = px.bar(df, x='startedAt', y=[1]*len(df), color='status', 
                                 title="EXECUTION_HISTORY", color_discrete_map={'success': '#00FF41', 'failed': '#FF0000'})
                    fig.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='#00FF41')
                    st.plotly_chart(fig, use_container_width=True)
                with col_b:
                    success_rate = len(df[df['status']=='success']) / len(df) * 100
                    st.metric("SUCCESS_RATE", f"{success_rate:.1f}%")
                    st.metric("AVG_LATENCY", f"{random.randint(150, 400)}ms")
            else:
                st.info("NO_DATA_STREAMS_FOUND")
                
        with t2:
            for e in get_executions(wf['id']):
                with st.expander(f"ID: {e['id']} | {e['status'].upper()}"):
                    st.json(e)
                    
        with t3:
            for node in wf.get('nodes', []):
                st.markdown(f"""
                <div class='terminal-card'>
                    <h3>NODE: {node['name']}</h3>
                    <p>TYPE: {node['type']}</p>
                    <p>STATUS: ONLINE</p>
                </div>
                """, unsafe_allow_html=True)

elif st.session_state.view == "SETTINGS":
    st.markdown("<h1 class='glow'>> SYSTEM_CONFIGURATION</h1>", unsafe_allow_html=True)
    sys_cfg = st.secrets.get("system", {})
    st.checkbox("ENABLE_NEURAL_LINK", value=sys_cfg.get("neural_link", True))
    st.checkbox("ENCRYPT_DATA_STREAMS", value=sys_cfg.get("encryption_enabled", True))
    st.slider("SIGNAL_STRENGTH", 0, 100, sys_cfg.get("signal_strength", 85))
    st.selectbox("TERMINAL_THEME", ["MATRIX_GREEN", "ZION_BLUE", "REBEL_RED"], index=0)

# --- FOOTER ---
st.sidebar.markdown("---")
st.sidebar.caption("MATRIX_OS // VER_4.0.0")
st.sidebar.caption("© 2199 Zion Mainframe")
