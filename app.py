# =============================
#  app.py - Streamlit Dashboard
# =============================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Client & Finance Dashboard", layout="wide")

st.title("📊 Strategic & Financial Analysis Dashboard")

# =============================
#  Load Data
# =============================
@st.cache_data
def load_data():
    clients = pd.read_excel("clients.xlsx")
    finance = pd.read_excel("finance.xlsx")
    return clients, finance

clients, finance = load_data()

# =============================
#  Clean Client Data
# =============================
clients.columns = clients.columns.str.strip()
clients.rename(columns={
    "Company Name": "Company",
    "Department": "Department",
    "Renewal Number": "Renewal_No",
    "Renewal Date": "Renewal_Date"
}, inplace=True)

clients["Renewal_Date"] = pd.to_datetime(clients["Renewal_Date"].astype(str) + "-01-01", errors="coerce")
clients["Year"] = clients["Renewal_Date"].dt.year
clients = clients.dropna(subset=["Company", "Department", "Year"])

# =============================
#  Clean Finance Data
# =============================
finance.columns = finance.columns.str.strip()
finance["Year"] = finance["Year"].astype(int)

# =============================
#  1. Active Clients by Year
# =============================
st.subheader("1️⃣ Active Clients by Year")
clients_per_year = clients.groupby("Year")["Company"].nunique().reset_index(name="Active_Clients")
clients_per_year["Growth_%"] = (clients_per_year["Active_Clients"].pct_change() * 100).round(1)

fig1 = px.bar(
    clients_per_year, x="Year", y="Active_Clients", text="Active_Clients",
    title="Active Clients by Year", template="plotly_white",
    color_discrete_sequence=["#0077b6"]
)
fig1.update_traces(textposition="outside")
st.plotly_chart(fig1, use_container_width=True)

# =============================
#  3. Market Share by Department
# =============================
st.subheader("3️⃣ Market Concentration by Contract Count")
dept_share = clients.groupby("Department")["Company"].count().reset_index(name="Total_Contracts")
dept_share["Share_%"] = round(100 * dept_share["Total_Contracts"] / dept_share["Total_Contracts"].sum(), 1)

fig3 = px.pie(
    dept_share, names="Department", values="Total_Contracts",
    title="Market Concentration by Contract Count", hole=0.45, template="plotly_white"
)
fig3.update_traces(textinfo="label+percent", pull=[0.05]*len(dept_share))
st.plotly_chart(fig3, use_container_width=True)

# =============================
#  4. First Contracts Only
# =============================
st.subheader("4️⃣ Market Concentration by First Contracts")
first_contracts = clients[clients["Renewal_No"] == 0]
first_share = first_contracts.groupby("Department")["Company"].count().reset_index(name="First_Contracts")
first_share["Share_%"] = round(100 * first_share["First_Contracts"] / first_share["First_Contracts"].sum(), 1)

fig4 = px.pie(
    first_share, names="Department", values="First_Contracts",
    title="Market Concentration by First Contracts Only", hole=0.45, template="plotly_white"
)
fig4.update_traces(textinfo="label+percent", pull=[0.05]*len(first_share))
st.plotly_chart(fig4, use_container_width=True)

# =============================
#  5. Client Retention
# =============================
st.subheader("5️⃣ Yearly Client Churn & Retention")
years = sorted(clients["Year"].unique())
churn_data = []
for i, year in enumerate(years[:-1]):
    current = set(clients[clients["Year"] == year]["Company"])
    next_year = set(clients[clients["Year"] == years[i+1]]["Company"])
    if len(current) > 0:
        churn_rate = round(100 * len(current - next_year) / len(current), 1)
        retention_rate = 100 - churn_rate
    else:
        churn_rate = retention_rate = np.nan
    churn_data.append({"Year": year, "Churn_%": churn_rate, "Retention_%": retention_rate})

churn_df = pd.DataFrame(churn_data)

fig5 = go.Figure()
fig5.add_trace(go.Scatter(x=churn_df["Year"], y=churn_df["Churn_%"],
                          mode="lines+markers", name="Churn Rate (%)",
                          line=dict(color="#ef476f", width=3)))
fig5.add_trace(go.Scatter(x=churn_df["Year"], y=churn_df["Retention_%"],
                          mode="lines+markers", name="Retention Rate (%)",
                          line=dict(color="#06d6a0", width=3)))
fig5.update_layout(title="Yearly Client Churn and Retention Rates",
                   xaxis_title="Year", yaxis_title="Rate (%)", template="plotly_white")
st.plotly_chart(fig5, use_container_width=True)

# =============================
#  6. Financial Performance
# =============================
st.subheader("6️⃣ Financial Performance by Department")
fig6 = px.bar(finance, x="Year", y="Total Sales", color="Department",
              title="Total Sales by Department and Year", template="plotly_white", barmode="group")
st.plotly_chart(fig6, use_container_width=True)

fig7 = px.bar(finance, x="Year", y="Total Profit", color="Department",
              title="Total Profit by Department and Year", template="plotly_white", barmode="group")
st.plotly_chart(fig7, use_container_width=True)

finance["Profit Margin_%"] = round((finance["Total Profit"] / finance["Total Sales"]) * 100, 1)
fig8 = px.line(finance, x="Year", y="Profit Margin_%", color="Department",
               title="Profit Margin by Department", markers=True, template="plotly_white")
st.plotly_chart(fig8, use_container_width=True)

# =============================
#  6. Financial Performance
# =============================
fig6 = px.bar(finance, x="Year", y="Total Sales", color="Department",
              title="Total Sales by Department and Year",
              template="plotly_white", barmode="group")
fig6.show()

fig7 = px.bar(finance, x="Year", y="Total Profit", color="Department",
              title="Total Profit by Department and Year",
              template="plotly_white", barmode="group")
fig7.show()

finance["Profit Margin_%"] = round((finance["Total Profit"] / finance["Total Sales"]) * 100, 1)

fig8 = px.line(finance, x="Year", y="Profit Margin_%", color="Department",
               title="Profit Margin by Department", markers=True, template="plotly_white")
fig8.show()

# =============================
#  9. Summary Overview
# =============================
summary = finance.groupby("Department")[["Total Sales", "Total Profit"]].sum().reset_index()
summary["Overall Margin_%"] = round((summary["Total Profit"] / summary["Total Sales"]) * 100, 1)
display(summary)

# =============================
#  7. Correlation Between Contracts & Financial Performance
# =============================

# ---- Version 1: Based on Total Contracts (includes renewals) ----
contracts_by_dept_all = clients.groupby(["Department", "Year"])["Company"].count().reset_index(name="Contracts_Count")

merged_all = pd.merge(contracts_by_dept_all, finance, on=["Department", "Year"], how="left")

corr_sales_all = merged_all["Contracts_Count"].corr(merged_all["Total Sales"])
corr_profit_all = merged_all["Contracts_Count"].corr(merged_all["Total Profit"])

print("🔹 Correlation based on ALL Contracts (including renewals):")
print(f"   ↳ Contracts vs Sales:  {corr_sales_all:.2f}")
print(f"   ↳ Contracts vs Profit: {corr_profit_all:.2f}\n")

fig_corr1 = px.scatter(
    merged_all, x="Contracts_Count", y="Total Sales", color="Department",
    trendline="ols", title="Correlation (All Contracts) Between Contracts Count and Total Sales",
    template="plotly_white", hover_data=["Year"]
)
fig_corr1.show()

fig_corr2 = px.scatter(
    merged_all, x="Contracts_Count", y="Total Profit", color="Department",
    trendline="ols", title="Correlation (All Contracts) Between Contracts Count and Total Profit",
    template="plotly_white", hover_data=["Year"]
)
fig_corr2.show()

# =============================
#  8. Service Mix & Client Distribution
# =============================
clients["Client_Type"] = np.where(clients["Renewal_No"] == 0, "New Client", "Renewed Client")

service_mix = clients.groupby(["Department", "Client_Type"])["Company"].nunique().reset_index(name="Client_Count")

total_per_dept = service_mix.groupby("Department")["Client_Count"].transform("sum")
service_mix["Share_%"] = round(100 * service_mix["Client_Count"] / total_per_dept, 1)

fig11 = px.bar(
    service_mix, x="Department", y="Client_Count", color="Client_Type", text="Share_%",
    title="Service Mix and Client Distribution (New vs Renewed Clients)",
    template="plotly_white", barmode="stack"
)
fig11.update_traces(textposition="outside")
fig11.show()



print("✅ Full Strategic & Financial Analysis Completed — No duplicates were removed, all contracts included.")

