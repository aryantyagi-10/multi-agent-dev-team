import os
import time
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://fastapi_backend:8000")

st.set_page_config(page_title="Multi-Agent Dev Team", layout="wide")

# ---- session state ----
for key, default in {
    "token": None, "username": None, "job_id": None,
    "logs": [], "next_index": 0, "job_status": None,
}.items():
    st.session_state.setdefault(key, default)


def auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}


# ---- auth UI ----
def auth_view():
    st.title("🤖 Multi-Agent Software Dev Team")
    tab_login, tab_reg = st.tabs(["Login", "Register"])

    with tab_login:
        u = st.text_input("Username", key="login_u")
        p = st.text_input("Password", type="password", key="login_p")
        if st.button("Login"):
            r = requests.post(
                f"{BACKEND_URL}/auth/login",
                data={"username": u, "password": p},
            )
            if r.ok:
                st.session_state.token = r.json()["access_token"]
                st.session_state.username = u
                st.rerun()
            else:
                st.error(r.json().get("detail", "Login failed"))

    with tab_reg:
        u2 = st.text_input("New username", key="reg_u")
        p2 = st.text_input("New password", type="password", key="reg_p")
        if st.button("Register"):
            r = requests.post(
                f"{BACKEND_URL}/auth/register",
                json={"username": u2, "password": p2},
            )
            if r.ok:
                st.session_state.token = r.json()["access_token"]
                st.session_state.username = u2
                st.rerun()
            else:
                st.error(r.json().get("detail", "Registration failed"))


# ---- main dashboard ----
def dashboard():
    st.sidebar.success(f"Logged in as {st.session_state.username}")
    if st.sidebar.button("Logout"):
        # Fixed: Explicitly resetting states back to their original type baselines
        st.session_state.token = None
        st.session_state.username = None
        st.session_state.job_id = None
        st.session_state.logs = []
        st.session_state.next_index = 0
        st.session_state.job_status = None
        st.rerun()

    st.title("🚀 Feature Request Console")
    prompt = st.text_area(
        "Describe the software feature you want built:",
        placeholder="e.g. A FastAPI endpoint that validates and stores email subscriptions.",
        height=120,
    )
    if st.button("Submit to Agent Team", type="primary"):
        r = requests.post(
            f"{BACKEND_URL}/jobs",
            json={"prompt": prompt},
            headers=auth_headers(),
        )
        if r.ok:
            st.session_state.job_id = r.json()["id"]
            st.session_state.logs = []
            st.session_state.next_index = 0
            st.session_state.job_status = "queued"
            st.rerun()
        else:
            st.error(r.json().get("detail", "Submission failed"))

    if st.session_state.job_id:
        render_live_feed()


def render_live_feed():
    st.divider()
    st.subheader(f"🧠 Agent Activity — Job {st.session_state.job_id[:8]}")
    status_box = st.empty()
    feed = st.container()

    # Poll loop without freezing: short bounded fetch per rerun
    r = requests.get(
        f"{BACKEND_URL}/jobs/{st.session_state.job_id}/logs",
        params={"after": st.session_state.next_index},
        headers=auth_headers(),
    )
    if r.ok:
        data = r.json()
        st.session_state.logs.extend(data["logs"])
        st.session_state.next_index = data["next_index"]
        st.session_state.job_status = data["status"]

    status_box.info(f"Status: **{st.session_state.job_status}**")

    icons = {"ProductManager": "📋", "Developer": "💻", "QAEngineer": "🧪", "System": "⚙️"}
    with feed:
        for entry in st.session_state.logs:
            # Handle list strings safely if raw logging text slips in
            if isinstance(entry, str):
                st.markdown(entry)
                continue
            icon = icons.get(entry.get("agent"), "🔹")
            with st.chat_message(entry.get("agent", "Agent"), avatar=icon):
                st.markdown(f"**{entry.get('agent')}**: {entry.get('message')}")

    if st.session_state.job_status in ("done", "failed"):
        job = requests.get(
            f"{BACKEND_URL}/jobs/{st.session_state.job_id}",
            headers=auth_headers(),
        ).json()
        if st.session_state.job_status == "done":
            st.success("✅ Job finished")
        else:
            st.error("❌ Job failed")
            
        with st.expander("📄 Generated code (main.py)", expanded=True):
            st.code(job.get("result_code", ""), language="python")
        with st.expander("🧪 Generated tests (test_main.py)"):
            st.code(job.get("result_tests", ""), language="python")
    else:
        time.sleep(2)
        st.rerun()


if st.session_state.token:
    dashboard()
else:
    auth_view()