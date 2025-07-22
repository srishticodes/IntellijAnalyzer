import streamlit as st
import requests
import pandas as pd
import altair as alt
from collections import Counter

API_URL = "http://localhost:9000"

st.set_page_config(page_title="IntellijAnalyzer Dashboard", layout="wide")
st.title("Intelligent Receipt and Bill Analyzer")


st.header("Upload Receipt or Bill")
st.markdown("**Limit 10MB per file • JPG, JPEG, PNG, PDF, TXT**")
uploaded_file = st.file_uploader(
    "Choose a file to upload",
    type=["jpg", "jpeg", "png", "pdf", "txt"]
)
if uploaded_file:
    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
    try:
        with st.spinner("Uploading and processing..."):
            resp = requests.post(f"{API_URL}/upload/", files=files, timeout=120)
        if resp.status_code == 200:
            st.success("File uploaded and processed successfully!")
        else:
            try:
                error_detail = resp.json().get('detail', 'Unknown error')
            except Exception:
                error_detail = resp.text
            st.error(f"Error: {error_detail}")
    except requests.exceptions.Timeout:
        st.error("Upload timed out. The file may be too large or the server is slow.")
    except Exception as e:
        st.error(f"Unexpected error during upload: {e}")


st.header("Uploaded Receipts and Bills")
receipts_resp = requests.get(f"{API_URL}/transactions/")
receipts_data = []
if receipts_resp.status_code == 200:
    receipts_data = receipts_resp.json().get("transactions", [])
    if receipts_data:
        receipts_df = pd.DataFrame(receipts_data)
        st.dataframe(receipts_df)
    else:
        st.info("No receipts uploaded yet.")
else:
    st.error("Failed to fetch receipts from backend.")


st.header("Tabular View: Parsed Transactions")
trans_resp = requests.get(f"{API_URL}/transactions/sorted/?sort_by=date&order=desc")
data = []
if trans_resp.status_code == 200:
    data = trans_resp.json().get("transactions", [])
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df)
    else:
        st.info("No transactions found.")
else:
    st.error("Failed to fetch transactions from backend.")
    data = []


st.header("Statistical Visualizations")

if data:
    vendor_freq = Counter([t['vendor'] for t in data if t.get('vendor')])
    if vendor_freq:
        st.subheader("Vendor Frequency Distribution (Bar Chart)")
        vendor_df = pd.DataFrame(list(vendor_freq.items()), columns=["Vendor", "Count"])
        st.bar_chart(vendor_df.set_index("Vendor"))
 
    cat_freq = Counter([t['category'] for t in data if t.get('category')])
    if cat_freq:
        st.subheader("Category Distribution (Pie Chart)")
        cat_df = pd.DataFrame(list(cat_freq.items()), columns=["Category", "Count"])
        st.altair_chart(
            alt.Chart(cat_df).mark_arc().encode(
                theta=alt.Theta(field="Count", type="quantitative"),
                color=alt.Color(field="Category", type="nominal")
            ), use_container_width=True
        )
else:
    st.info("No data for statistical visualizations.")


st.header("Time-Series Expenditure Trend")
stats_resp = requests.get(f"{API_URL}/transactions/stats/")
if stats_resp.status_code == 200:
    stats = stats_resp.json()
    monthly = stats.get("monthly_totals", {})
    moving_avg = stats.get("monthly_moving_avg", {})
    if monthly:
        st.subheader("Monthly Spend Trend (with Moving Average)")
        monthly_df = pd.DataFrame(sorted(monthly.items()), columns=["Month", "Total Spend"])
        chart = alt.Chart(monthly_df).mark_line(point=True).encode(
            x="Month",
            y=alt.Y("Total Spend", axis=alt.Axis(title="Total Spend")),
            tooltip=["Month", "Total Spend"]
        ).properties(title="Monthly Spend")
        if moving_avg:
            ma_df = pd.DataFrame(sorted(moving_avg.items()), columns=["Month", "Moving Average"])
            ma_chart = alt.Chart(ma_df).mark_line(color="orange").encode(
                x="Month",
                y=alt.Y("Moving Average", axis=alt.Axis(title="Moving Average")),
                tooltip=["Month", "Moving Average"]
            )
            chart = chart + ma_chart
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No monthly spend data available.")
else:
    st.error("Failed to fetch statistics from backend.") 