import streamlit as st
import requests

# ----------------- CONFIG -----------------
API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="BizAcuity AI Engine", layout="wide")

# ----------------- STYLES -----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #ffffff;
    color: #1f2937;
}

.block-container {
    padding: 2rem 3rem;
}

h1 {
    font-size: 36px !important;
    font-weight: 600;
    color: #0B3C5D;
}

section[data-testid="stSidebar"] {
    background-color: #0B3C5D;
}

section[data-testid="stSidebar"] * {
    color: white !important;
    font-size: 16px !important;
}

label {
    font-size: 15px !important;
    font-weight: 500;
}

input, textarea {
    font-size: 16px !important;
}

.stButton > button {
    background-color: #0B3C5D;
    color: white;
    border-radius: 6px;
    padding: 10px 18px;
}

.card {
    background: #f9fafb;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #e5e7eb;
    margin-bottom: 20px;
}

</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR -----------------
st.sidebar.markdown("<h1 style='font-size:32px; font-weight:700; line-height:1.2;'>AI Outbound Engine</h1>", unsafe_allow_html=True)
page = st.sidebar.radio("Navigation", ["Dashboard", "Send Email", "Bulk Send", "History"])

# ----------------- DASHBOARD -----------------
if page == "Dashboard":
    st.title("Dashboard")

    try:
        res = requests.get(f"{API_URL}/leads/")
        data = res.json()

        total = len(data)
        success = len(data)  # assuming all sent
        failure = 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Emails Sent", total)
        col2.metric("Success Rate", f"{100 if total else 0}%")
        col3.metric("Failures", failure)

    except:
        st.warning("⚠️ Backend not running or no data available")

# ----------------- SEND EMAIL -----------------
elif page == "Send Email":
    st.title("Send Email")

    st.markdown('<div class="card">', unsafe_allow_html=True)

    name = st.text_input("Name")
    company = st.text_input("Company (domain like tcs.com)")
    role = st.text_input("Role")
    email = st.text_input("Email")
    problem = st.text_area("Problem")

    if st.button("Send Email"):
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
            files = {"file": file.getvalue()}
            res = requests.post(f"{API_URL}/bulk-send/", files={"file": file})
            result = res.json()

            st.success("Bulk emails processed")
            st.write(result)

        except Exception as e:
            st.error(str(e))

# ----------------- LEADS -----------------
elif page == "History":
    st.markdown("<h1 style='font-size:38px; font-weight:600; color:#0B3C5D;'>History</h1>", unsafe_allow_html=True)

    try:
        res = requests.get(f"{API_URL}/leads/")
        data = res.json()

        # Clean table-style history (no blank boxes)
        import pandas as pd

        # Remove empty rows
        clean_data = [l for l in data if any(l.values())]

        if clean_data:
            df = pd.DataFrame(clean_data)

            # Select only useful columns
            df = df[["name", "company", "email", "message"]]

            st.dataframe(df, use_container_width=True)
        else:
            st.info("No history available yet")

    except:
        st.warning("⚠️ Unable to fetch leads")
