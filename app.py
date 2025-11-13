# =============================
#  Streamlit Dashboard for Proserv
# =============================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Proserv Dashboard", layout="wide")

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
#  Dashboard Sections
# =============================
st.title("📊 Proserv Strategic & Financial Dashboard")

# -----------------------------
st.header("1️⃣ Active Clients by Year")
clients_per_year = clients.groupby("Year")["Company"].nunique().reset_index(name="Active_Clients")
clients_per_year["Growth_%"] = (clients_per_year["Active_Clients"].pct_change() * 100).round(1)
fig1 = px.bar(clients_per_year, x="Year", y="Active_Clients", text="Active_Clients",
              color_discrete_sequence=["#0077b6"], template="plotly_white")
fig1.update_traces(textposition="outside")
st.plotly_chart(fig1, use_container_width=True)

# -----------------------------
st.header("2️⃣ Renewal Frequency")
renewal_counts = clients.groupby("Company")["Renewal_No"].max().value_counts().sort_index().reset_index()
renewal_counts.columns = ["Renewal_Times", "Number_of_Clients"]
fig2 = px.bar(renewal_counts, x="Renewal_Times", y="Number_of_Clients",
              text="Number_of_Clients", color_discrete_sequence=["#00b4d8"], template="plotly_white")
fig2.update_traces(textposition="outside")
st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
st.header("3️⃣ Market Share by Department (All Contracts)")
dept_share = clients.groupby("Department")["Company"].count().reset_index(name="Total_Contracts")
fig3 = px.pie(dept_share, names="Department", values="Total_Contracts", hole=0.45,
              template="plotly_white", title="Market Concentration by Contract Count")
fig3.update_traces(textinfo="label+percent", pull=[0.05]*len(dept_share))
st.plotly_chart(fig3, use_container_width=True)

# -----------------------------
st.header("4️⃣ Key Clients Contribution Estimate")
client_contracts = clients.groupby(["Department", "Company"])["Renewal_No"].max().reset_index()
client_contracts["Total_Contracts"] = client_contracts["Renewal_No"] + 1
merged_clients_profit = pd.merge(client_contracts, finance[["Department", "Year", "Total Profit"]],
                                 on="Department", how="left")
dept_totals = client_contracts.groupby("Department")["Total_Contracts"].sum().reset_index(name="Dept_Total_Contracts")
merged_clients_profit = pd.merge(merged_clients_profit, dept_totals, on="Department", how="left")
merged_clients_profit["Contracts_Share_%"] = round(100 * merged_clients_profit["Total_Contracts"] / merged_clients_profit["Dept_Total_Contracts"], 1)
merged_clients_profit["Estimated_Profit"] = round(merged_clients_profit["Contracts_Share_%"] / 100 * merged_clients_profit["Total Profit"], 2)
top_clients_per_dept = merged_clients_profit.sort_values(["Department", "Estimated_Profit"], ascending=[True, False])
top_clients_15 = top_clients_per_dept.groupby("Department").head(15).reset_index(drop=True)

fig_top15 = px.bar(
    top_clients_15.sort_values(["Department", "Estimated_Profit"], ascending=[True, False]),
    x="Department",
    y="Estimated_Profit",
    color="Company",
    text="Estimated_Profit",
    labels={"Estimated_Profit": "Estimated Profit (EGP)", "Department": "Department"},
    template="plotly_white",
    height=600,
    title="Top 15 Clients Contribution per Department"
)
fig_top15.update_traces(textposition="inside")
st.plotly_chart(fig_top15, use_container_width=True)

# -----------------------------
st.header("5️⃣ Financial Performance Overview")
st.dataframe(finance)

st.success("✅ Dashboard Loaded Successfully")
