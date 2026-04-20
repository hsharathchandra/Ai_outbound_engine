import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="BizAcuity AI Engine", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #ffffff;
    color: #1f2937;
}
.block-container { padding: 2rem 3rem; }
h1 { font-size: 36px !important; font-weight: 600; color: #0B3C5D; }
section[data-testid="stSidebar"] { background-color: #0B3C5D; }
section[data-testid="stSidebar"] * { color: white !important; font-size: 16px !important; }
label { font-size: 15px !important; font-weight: 500; }
input, textarea { font-size: 16px !important; }
.stButton > button {
    background-color: #0B3C5D; color: white;
    border-radius: 6px; padding: 10px 18px;
}
.card {
    background: #f9fafb; padding: 20px;
    border-radius: 8px; border: 1px solid #e5e7eb; margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown(
    "<h1 style='font-size:32px; font-weight:700; line-height:1.2;'>AI Outbound Engine</h1>",
    unsafe_allow_html=True
)
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Send Email", "Bulk Send", "History", "Leads Engine (MVP)"]
)

# ----------------- DASHBOARD -----------------
if page == "Dashboard":
    st.title("Dashboard")
    try:
        res = requests.get(f"{API_URL}/leads/")
        data = res.json()
        total = len(data)
        col1, col2, col3 = st.columns(3)
        col1.metric("Emails Sent", total)
        col2.metric("Success Rate", f"{100 if total else 0}%")
        col3.metric("Failures", 0)
    except Exception:
        st.warning("⚠️ Backend not running or no data available")

# ----------------- SEND EMAIL -----------------
elif page == "Send Email":
    st.title("Send Email")
    st.markdown('<div class="card">', unsafe_allow_html=True)

    name = st.text_input("Name")
    company = st.text_input("Company (domain like tcs.com)")
    # FIX: role was missing — caused NameError
    role = st.text_input("Role (e.g. CEO, Head of Sales)")
    email = st.text_input("Email")
    problem = st.text_area("Problem")

    if st.button("Send Email"):
        if not all([name, company, role, email]):
            st.error("Please fill in all required fields.")
        else:
            payload = {
                "name": name,
                "company": company,
                "role": role,
                "email": email,
                "problem": problem
            }
            try:
                res = requests.post(f"{API_URL}/send-email/", json=payload)
                result = res.json()
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    st.success("Email Sent!")
                    st.write("Subject:", result.get("subject"))
                    st.write("Message:", result.get("message"))
            except Exception as e:
                st.error(str(e))

    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- BULK SEND -----------------
elif page == "Bulk Send":
    st.title("Bulk Email Sender")
    file = st.file_uploader("Upload CSV", type=["csv"])

    if file and st.button("Send Bulk Emails"):
        try:
            res = requests.post(f"{API_URL}/bulk-send/", files={"file": file})
            result = res.json()
            st.success("Bulk emails processed")
            st.write(result)
        except Exception as e:
            st.error(str(e))

# ----------------- HISTORY -----------------
elif page == "History":
    st.markdown(
        "<h1 style='font-size:38px; font-weight:600; color:#0B3C5D;'>History</h1>",
        unsafe_allow_html=True
    )
    try:
        res = requests.get(f"{API_URL}/leads/")
        data = res.json()
        clean_data = [l for l in data if any(l.values())]
        if clean_data:
            df = pd.DataFrame(clean_data)
            df = df[["name", "company", "email", "message"]]
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No history available yet")
    except Exception:
        st.warning("⚠️ Unable to fetch leads")

# ----------------- LEADS ENGINE -----------------
elif page == "Leads Engine (MVP)":
    st.title("🚀 Leads Engine")

    col1, col2, col3 = st.columns(3)
    with col1:
        industry = st.text_input("Industry")
    with col3:
        region = st.text_input("Region")

    problem = st.text_area("Problem Statement")

    if "leads" not in st.session_state:
        st.session_state.leads = []
    if "companies" not in st.session_state:
        st.session_state.companies = []
    if "emails" not in st.session_state:
        st.session_state.emails = []

    if st.button("👉 Generate Leads"):
        if not industry or not region:
            st.error("Please enter both Industry and Region.")
        else:
            try:
                res = requests.post(f"{API_URL}/generate-leads/", json={
                    "industry": industry,
                    "region": region
                })
                data = res.json()
                st.session_state.companies = data.get("companies", [])
                st.session_state.leads = data.get("leads", [])
                st.success(f"✅ {len(st.session_state.leads)} leads generated")
            except Exception as e:
                st.error(f"Error generating leads: {str(e)}")

    if st.session_state.get("companies"):
        st.subheader("🏢 Companies")
        for c in st.session_state["companies"]:
            st.write(f"- {c}")

    if st.session_state.get("leads"):
        st.subheader("📊 Leads")
        df = pd.DataFrame(st.session_state.leads)
        if "domain" in df.columns:
            df = df.drop(columns=["domain"])
        st.dataframe(df, use_container_width=True)

    if st.session_state.leads and st.button("⚡ Generate Emails"):
        try:
            res = requests.post(f"{API_URL}/generate-emails/", json={
                "leads": st.session_state.leads,
                "problem": problem
            })
            st.session_state.emails = res.json().get("emails", [])
            st.success("Emails generated")
        except Exception as e:
            st.error(f"Error generating emails: {str(e)}")

    if st.session_state.emails:
        for i, e in enumerate(st.session_state.emails):
            st.markdown("---")
            e["subject"] = st.text_input("Subject", e.get("subject", ""), key=f"s{i}")
            e["message"] = st.text_area("Message", e.get("message", ""), key=f"m{i}")

    if st.session_state.emails and st.button("💾 Save Drafts"):
        try:
            requests.post(f"{API_URL}/save-drafts/", json={
                "emails": st.session_state.emails
            })
            st.success("Drafts saved")
        except Exception as e:
            st.error(str(e))

    if st.session_state.emails and st.button("🚀 Send Emails"):
        try:
            res = requests.post(f"{API_URL}/send-emails/", json={
                "emails": st.session_state.emails
            })
            st.success(f"Sent {res.json().get('sent', 0)} emails")
        except Exception as e:
            st.error(str(e))
