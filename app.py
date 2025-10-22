import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
from io import BytesIO

# =============================
#  Load Data
# =============================
from google.colab import files
uploaded = files.upload()  #  Upload your file (e.g., Proserv V.xlsx)
FILE_PATH = list(uploaded.keys())[0]

df = pd.read_excel(FILE_PATH)

# =============================
#  Clean & Prepare Data
# =============================
df.columns = df.columns.str.strip()
df.rename(columns={
    "Company Name": "Company",
    "Department": "Department",
    "Renewal Number": "Renewal_No",
    "Renewal Date": "Renewal_Date",
    "Contract Duration (Months)": "Duration_Months",
    "Cost": "Cost"
}, inplace=True)

# Keep % values as text (don’t convert)
df["Cost"] = df["Cost"].astype(str)

# Convert Renewal Date to datetime (year-based)
df["Renewal_Date"] = pd.to_datetime(df["Renewal_Date"].astype(str) + "-01-01", errors="coerce")
df["Year"] = df["Renewal_Date"].dt.year

# Remove rows without a valid company or year
df = df.dropna(subset=["Company", "Year"])

# Convert Cost safely (keep % rows intact)
df["Numeric_Cost"] = pd.to_numeric(df["Cost"].str.replace("[^0-9.]", "", regex=True), errors="coerce")

# =============================
#  Exclude Outsource from financial calculations
# =============================
df_financial = df[df["Department"].str.lower() != "outsource"].copy()


# =============================
#  Helper: format percentage
# =============================
def fmt(x):
    if pd.isna(x):
        return ""
    return f"{x*100:.0f}%"

# =============================
#  1. Customer Turnover (2013–2024, 2013–2018, 2019–2024)
# =============================
periods = {"2013–2024": (2013, 2024), "2013–2018": (2013, 2018), "2019–2024": (2019, 2024)}
stats = []
for label, (s, e) in periods.items():
    start_clients = set(df[df["Year"] == s]["Company"])
    end_clients = set(df[df["Year"] == e]["Company"])
    period_clients = set(df[(df["Year"] >= s) & (df["Year"] <= e)]["Company"])
    churn = len(start_clients - end_clients) / len(start_clients) if len(start_clients) > 0 else np.nan
    retention = 1 - churn if not np.isnan(churn) else np.nan
    stats.append({
        "Period": label,
        "Start_Clients": len(start_clients),
        "End_Clients": len(end_clients),
        "Clients_in_Period": len(period_clients),
        "Churn_Rate(%)": round(churn * 100, 1) if pd.notna(churn) else None,
        "Retention_Rate(%)": round(retention * 100, 1) if pd.notna(retention) else None
    })
period_df = pd.DataFrame(stats)
display(period_df)

# Visualization
fig1 = px.bar(period_df, x="Period", y="Churn_Rate(%)", color="Period",
              title="Customer Turnover Rate by Period",
              text="Churn_Rate(%)", template="plotly_white")
fig1.show()

# =============================
#  2. Annual Retention & Churn
# =============================
years = sorted(df["Year"].dropna().unique())
annual = []
for i, y in enumerate(years[:-1]):
    a = set(df[df["Year"] == y]["Company"])
    b = set(df[df["Year"] == years[i + 1]]["Company"])
    churn_rate = len(a - b) / len(a) if len(a) else np.nan
    retention_rate = 1 - churn_rate if pd.notna(churn_rate) else np.nan
    annual.append({
        "Year": y,
        "Active_Clients": len(a),
        "Churn_Rate(%)": round(churn_rate * 100, 1),
        "Retention_Rate(%)": round(retention_rate * 100, 1)
    })
annual_df = pd.DataFrame(annual)
display(annual_df)

fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=annual_df["Year"], y=annual_df["Churn_Rate(%)"], mode="lines+markers", name="Churn Rate"))
fig2.add_trace(go.Scatter(x=annual_df["Year"], y=annual_df["Retention_Rate(%)"], mode="lines+markers", name="Retention Rate"))
fig2.update_layout(title="Annual Customer Churn and Retention", template="plotly_white", xaxis_title="Year", yaxis_title="Rate (%)")
fig2.show()

# =============================
#  3. Customer Growth Over Years
# =============================
client_growth = df.groupby("Year")["Company"].nunique().reset_index(name="Active_Clients")
client_growth["Growth(%)"] = client_growth["Active_Clients"].pct_change() * 100
display(client_growth)

fig3 = px.bar(client_growth, x="Year", y="Active_Clients", title="Customer Growth Over Years", text="Active_Clients", template="plotly_white")
fig3.show()

# =============================
#  4. Business Volume Growth
# =============================
revenue_growth = df_financial.groupby("Year")["Numeric_Cost"].sum().reset_index(name="Total_Cost")
revenue_growth["Growth(%)"] = revenue_growth["Total_Cost"].pct_change() * 100
display(revenue_growth)

fig4 = px.line(revenue_growth, x="Year", y="Total_Cost", markers=True, title="Business Volume Growth Over Years", template="plotly_white")
fig4.show()

# =============================
#  5. Top 15 Customers by Total Cost
# =============================
top_customers = df_financial.groupby("Company")["Numeric_Cost"].sum().sort_values(ascending=False).head(15).reset_index()

fig5 = px.bar(top_customers, x="Company", y="Numeric_Cost", title="Top 15 Customers by Total Cost", text_auto=".2s", template="plotly_white")
fig5.update_layout(xaxis_tickangle=-45)
fig5.show()

# =============================
#  6. Most Active Companies (by renewals)
# =============================
active_companies = df["Company"].value_counts().head(15).reset_index()
active_companies.columns = ["Company", "Renewal_Count"]
display(active_companies)

fig6 = px.bar(active_companies, x="Company", y="Renewal_Count", title="Most Active Companies (by Renewals)", text="Renewal_Count", template="plotly_white")
fig6.update_layout(xaxis_tickangle=-45)
fig6.show()

# =============================
#  7. Department Distribution (Without Service Details)
# =============================
dept_clients = df.groupby("Department")["Company"].nunique().reset_index(name="Unique_Clients")
display(dept_clients)

fig7 = px.bar(dept_clients, x="Department", y="Unique_Clients",
              title="Department Distribution (Unique Clients)",
              text="Unique_Clients", template="plotly_white")
fig7.update_layout(xaxis_tickangle=-30)
fig7.show()


# =============================
#  8. Market Concentration Ratio
# =============================
dept_market = df_financial.groupby("Department")["Numeric_Cost"].sum().reset_index()
dept_market["Share(%)"] = 100 * dept_market["Numeric_Cost"] / dept_market["Numeric_Cost"].sum()


fig8 = px.pie(dept_market, names="Department", values="Share(%)",
              title="Market Concentration by Department", template="plotly_white", hole=0.3)
fig8.show()

print(" Full analysis completed successfully.")


