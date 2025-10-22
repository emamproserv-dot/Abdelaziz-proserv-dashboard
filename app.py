import streamlit as st
import pandas as pd
import plotly.express as px

# =============================
#  LOAD DATA
# =============================
uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx", "csv"])
if uploaded_file is not None:
    if uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file)

    # تحويل تاريخ التجديد إلى صيغة تاريخ
    df["Renewal Date"] = pd.to_datetime(df["Renewal Date"].astype(str) + "-01-01", errors="coerce")

    # =============================
    #  DASHBOARD STRUCTURE
    # =============================
    st.set_page_config(page_title="Proserv Dashboard", layout="wide")

    st.title("📊 Proserv V Dashboard")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Dashboard Overview",
        "Customer Trends",
        "Revenue Analytics",
        "Outsource Summary"
    ])

    # =============================
    #  TAB 1 - Overview
    # =============================
    with tab1:
        st.header("📈 Dashboard Overview")

        years = sorted(df["Renewal Date"].dt.year.dropna().unique())
        selected_year = st.selectbox("Select Year", years)

        df_year = df[df["Renewal Date"].dt.year == selected_year]

        st.metric("Total Contracts", len(df_year))
        st.metric("Unique Clients", df_year["Client Name"].nunique())

        fig = px.bar(
            df_year.groupby("Service Type").size().reset_index(name="Count"),
            x="Service Type",
            y="Count",
            title=f"Contracts by Service Type ({selected_year})"
        )
        st.plotly_chart(fig, use_container_width=True)

    # =============================
    #  TAB 2 - Customer Trends
    # =============================
    with tab2:
        st.header("📊 Customer Trends")

        trend = df.groupby(df["Renewal Date"].dt.year).size().reset_index(name="Contracts")
        fig2 = px.line(trend, x="Renewal Date", y="Contracts", title="Contracts Over Time")
        st.plotly_chart(fig2, use_container_width=True)

    # =============================
    #  TAB 3 - Revenue Analytics
    # =============================
    with tab3:
        st.header("💰 Revenue Analytics")

        if "Total Service Fee In EGP" in df.columns:
            rev = df.groupby(df["Renewal Date"].dt.year)["Total Service Fee In EGP"].sum().reset_index()
            fig3 = px.bar(rev, x="Renewal Date", y="Total Service Fee In EGP", title="Total Revenue Over Time")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.warning("Column 'Total Service Fee In EGP' not found in your file.")

    # =============================
    #  TAB 4 - Outsource Summary
    # =============================
    with tab4:
        st.header("👥 Outsource Summary")

        if "Service Type" in df.columns:
            outsource_df = df[df["Service Type"].str.contains("Outsource", case=False, na=False)]
            st.write(outsource_df)

            fig4 = px.pie(outsource_df, names="Client Name", title="Outsource Clients Distribution")
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.warning("Column 'Service Type' not found in your file.")

    # =============================
    #  DOWNLOAD DATA
    # =============================
    st.download_button("📥 Download filtered data (Excel)", df_year.to_csv(index=False).encode('utf-8'),
                       f"filtered_data_{selected_year}.csv", "text/csv")

else:
    st.info("👆 Please upload your Excel or CSV file to begin.")
