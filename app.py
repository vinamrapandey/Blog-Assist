import streamlit as st
import time
import threading
from datetime import datetime
from config_manager import ConfigManager
from llm_manager import LLMHandler
from wp_manager import WordPressHandler
from agent_scheduler import AgentScheduler

# --- Page Config ---
st.set_page_config(
    page_title="AI Blog Writer Agent",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Session State Initialization ---
if 'scheduler' not in st.session_state:
    st.session_state.scheduler = AgentScheduler()

if 'logs' not in st.session_state:
    st.session_state.logs = []

def log_message(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{timestamp}] {message}")

# --- Load Config ---
config = ConfigManager.load_config()

# --- Sidebar: Credentials & Settings ---
st.sidebar.title("⚙️ Settings")

st.sidebar.subheader("1. AI Provider")
llm_provider = st.sidebar.selectbox(
    "Select LLM Provider",
    ["Google Gemini", "OpenAI"],
    index=0 if config.get("llm_provider") == "Google Gemini" else 1
)

api_key = st.sidebar.text_input(
    f"{llm_provider} API Key",
    type="password",
    value=config.get("api_key", ""),
    help="Enter your API Key here."
)

if llm_provider == "OpenAI":
    st.sidebar.info("Note: OpenAI usage may incur costs. 'gpt-4o-mini' is used as the cost-effective model.")

st.sidebar.subheader("2. WordPress Credentials")
wp_url = st.sidebar.text_input(
    "WordPress Site URL",
    value=config.get("wp_url", ""),
    placeholder="https://your-site.com"
)
wp_user = st.sidebar.text_input(
    "Username",
    value=config.get("wp_user", "")
)
wp_password = st.sidebar.text_input(
    "Application Password",
    type="password",
    value=config.get("wp_password", ""),
    help="Generate this in WP Admin > Users > Profile > Application Passwords"
)

# Save Config Button
if st.sidebar.button("Save Configuration"):
    new_config = {
        "llm_provider": llm_provider,
        "api_key": api_key,
        "wp_url": wp_url,
        "wp_user": wp_user,
        "wp_password": wp_password
    }
    # Persist other settings too if they exist in session state
    if 'topic' in st.session_state: new_config['topic'] = st.session_state.topic
    
    ConfigManager.save_config(new_config)
    st.sidebar.success("Configuration saved!")

# --- Main Interface ---
st.title("✍️ AI Blog Writer Agent")
st.markdown("Automate your tech blog with AI-generated content published directly to WordPress.")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Agent Configuration")
    
    topic_options = ["Tech", "Travel", "Food", "Lifestyle", "Health", "Business", "Custom"]
    selected_topic = st.selectbox(
        "Blog Niche / Topic",
        topic_options,
        index=0
    )
    
    custom_topic = ""
    if selected_topic == "Custom":
        custom_topic = st.text_input("Enter Custom Topic", placeholder="e.g. Quantum Computing")
        final_topic = custom_topic
    else:
        final_topic = selected_topic

    word_count = st.number_input("Approximate Word Count", min_value=300, max_value=2000, value=500, step=100)
    
    schedule_interval = st.selectbox(
        "Automation Schedule (Hours)",
        [3, 6, 9, 12, 24, 48],
        index=4
    )

with col2:
    st.subheader("Agent Status")
    
    status_container = st.container()
    
    # Scheduler Controls
    c1, c2 = st.columns(2)
    with c1:
        start_btn = st.button("▶ Start Agent", type="primary", use_container_width=True)
    with c2:
        stop_btn = st.button("⏹ Stop Agent", type="secondary", use_container_width=True)

    if start_btn:
        if not api_key or not wp_url or not wp_user or not wp_password:
            st.error("Please configure all credentials in the sidebar first.")
        else:
            # wrapper function for the job
            def job_wrapper():
                log_message(f"Starting scheduled job for topic: {final_topic}")
                run_generation_cycle(llm_provider, api_key, final_topic, word_count, wp_url, wp_user, wp_password)
            
            st.session_state.scheduler.start(schedule_interval, job_wrapper)
            log_message(f"Agent started. Running every {schedule_interval} hours.")
            st.rerun()

    if stop_btn:
        st.session_state.scheduler.stop()
        log_message("Agent stopped.")
        st.rerun()

    # Display Status
    sched_status = st.session_state.scheduler.get_status()
    st.metric("Status", "Running" if sched_status["is_running"] else "Stopped")
    st.text(f"Next Run: {sched_status['next_run']}")
    st.text(f"Last Run: {sched_status['last_run']}")

    st.divider()
    st.subheader("Manual Control")
    if st.button("Run Once Now", use_container_width=True):
        if not api_key or not wp_url or not wp_user or not wp_password:
            st.error("Missing credentials.")
        else:
            log_message("Starting manual run...")
            run_generation_cycle(llm_provider, api_key, final_topic, word_count, wp_url, wp_user, wp_password)

# --- Core Logic Function ---
def run_generation_cycle(provider, key, topic, count, url, user, password):
    try:
        # 1. Generate Content
        log_message(f"Generating content for topic: {topic}...")
        llm = LLMHandler(provider, key)
        blog_data = llm.generate_blog(topic, count)
        
        if "error" in blog_data:
            log_message(f"LLM Error: {blog_data['error']}")
            return

        title = blog_data.get("title", "No Title")
        content = blog_data.get("content", "")
        log_message(f"Generated: {title}")

        # 2. Publish to WordPress
        log_message("Publishing to WordPress...")
        wp = WordPressHandler(url, user, password)
        result = wp.publish_post(title, content, status="draft") # Default to draft for safety
        
        if "id" in result:
             log_message(f"Success! Post ID: {result['id']} (Status: {result.get('status')})")
        else:
             log_message(f"WordPress Error: {result}")

    except Exception as e:
        log_message(f"Critical Error: {str(e)}")

# --- Logs Display ---
st.divider()
st.subheader("Activity Log")
log_container = st.container(height=200)
for log in reversed(st.session_state.logs):
    log_container.text(log)
