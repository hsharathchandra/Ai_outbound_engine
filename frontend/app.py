import streamlit as st
import requests

st.set_page_config(page_title="AI Outbound Engine", layout="wide")

# ---------------- SIDEBAR ----------------
st.sidebar.title("🚀 AI Outbound Engine")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Send Email", "Bulk Email", "History"]
)

# ---------------- DASHBOARD ----------------
if page == "Dashboard":
    st.title("📊 Dashboard")

    try:
        res = requests.get("http://127.0.0.1:8000/stats/")
        stats = res.json()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Emails Sent", stats.get("total", 0))

        with col2:
            st.metric("Success Rate", f"{stats.get('success_rate', 0)}%")

        with col3:
            st.metric("Replies", stats.get("replies", 0))

    except:
        st.warning("⚠️ Backend not running or no data available")

# ---------------- SEND EMAIL ----------------
elif page == "Send Email":
    st.title("📧 Send Personalized Email")

    name = st.text_input("Name")
    company = st.text_input("Company (use domain like tcs.com)")
    role = st.text_input("Role")
    email = st.text_input("Email")
    problem = st.text_area("Problem")

    if st.button("Generate & Send Email"):
        data = {
            "name": name,
            "company": company,
            "role": role,
            "email": email,
            "problem": problem,
        }

        try:
            res = requests.post("http://127.0.0.1:8000/send-email/", json=data)
            response = res.json()

            if "message" in response:
                st.success("✅ Email sent successfully!")

                st.subheader("Subject")
                st.info(response.get("subject", ""))

                st.subheader("Generated Email")
                st.text_area("", response["message"], height=300)

            elif "error" in response:
                st.error(response["error"])

            else:
                st.error("Unexpected response from server")

        except:
            st.error("❌ Backend not reachable")

# ---------------- BULK EMAIL ----------------
elif page == "Bulk Email":
    st.title("📂 Bulk Email Sender")

    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    if uploaded_file is not None:
        if st.button("Send Bulk Emails"):
            try:
                with st.spinner("Sending emails..."):
                    res = requests.post(
                        "http://127.0.0.1:8000/bulk-send/",
                        files={"file": uploaded_file}
                    )

                if res.status_code == 200:
                    results = res.json().get("results", [])

                    st.success("✅ Bulk sending completed!")

                    for r in results:
                        if r["status"] == "sent":
                            st.write(f"✅ {r['email']}")
                        else:
                            st.write(f"❌ {r['email']} - {r.get('error')}")

                else:
                    st.error("Bulk API failed")

            except:
                st.error("❌ Bulk send failed")

# ---------------- HISTORY ----------------
elif page == "History":
    st.title("📜 Email History")

    if st.button("Load History"):
        try:
            res = requests.get("http://127.0.0.1:8000/leads/")
            leads = res.json()

            if not leads:
                st.info("No data available yet")

            for lead in leads:
                st.subheader(lead.get("name", "Unknown"))

                st.write(f"**Company:** {lead.get('company', '')}")
                st.write(f"**Role:** {lead.get('role', '')}")
                st.write(f"**Email:** {lead.get('email', '')}")

                st.text_area(
                    "Message",
                    lead.get("message", ""),
                    height=150
                )

        except:
            st.error("❌ Failed to load history")