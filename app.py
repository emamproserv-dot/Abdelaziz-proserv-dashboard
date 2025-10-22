import streamlit as st
import pandas as pd
import plotly.express as px

# =============================
# إعداد الصفحة
# =============================
st.set_page_config(
    page_title="Proserv Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================
# تحميل البيانات
# =============================
@st.cache_data
def load_data():
    df = pd.read_excel("Proserv V - Copy.xlsx")
    return df

df = load_data()

st.title("📊 Proserv Dashboard")
st.markdown("عرض شامل للبيانات في صفحة واحدة مع تبويبات (Tabs)")

# =============================
# Tabs
# =============================
tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "🏢 Companies", "📅 Contracts", "📍 Sectors"])

# =============================
# Tab 1 – Overview
# =============================
with tab1:
    st.subheader("General Overview")
    st.metric("Total Companies", len(df["Company Name"].unique()))
    st.metric("Total Records", len(df))
    
    if "Service Type" in df.columns:
        service_counts = df["Service Type"].value_counts().reset_index()
        service_counts.columns = ["Service Type", "Count"]
        fig = px.pie(service_counts, names="Service Type", values="Count", title="Contracts by Service Type")
        st.plotly_chart(fig, use_container_width=True)

# =============================
# Tab 2 – Companies
# =============================
with tab2:
    st.subheader("Company Details")
    selected_company = st.selectbox("Select Company", sorted(df["Company Name"].unique()))
    company_data = df[df["Company Name"] == selected_company]
    st.dataframe(company_data, use_container_width=True)

# =============================
# Tab 3 – Contracts
# =============================
with tab3:
    st.subheader("Contract Analysis")
    if "Start Year" in df.columns:
        year_summary = df.groupby("Start Year").size().reset_index(name="Contracts")
        fig = px.bar(year_summary, x="Start Year", y="Contracts", title="Contracts by Start Year")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Column 'Start Year' not found in your dataset.")

# =============================
# Tab 4 – Sectors
# =============================
with tab4:
    st.subheader("Sector Distribution")
    if "Sector" in df.columns:
        sector_counts = df["Sector"].value_counts().reset_index()
        sector_counts.columns = ["Sector", "Count"]
        fig = px.bar(sector_counts, x="Sector", y="Count", title="Clients by Sector")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Column 'Sector' not found in your dataset.")
