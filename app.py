# =============================
#  Setup & Libraries
# =============================
!pip install -q plotly pandas openpyxl kaleido

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# =============================
#  Load Data
# =============================
clients = pd.read_excel("clients.xlsx")   # File 1: Client contracts & renewals
finance = pd.read_excel("finance.xlsx")   # File 2: Financial summary per Department

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

# ✅ قراءة السنة كصيغة تاريخ (كلها تعتبر بداية السنة)
clients["Renewal_Date"] = pd.to_datetime(clients["Renewal_Date"].astype(str) + "-01-01", errors="coerce")
clients["Year"] = clients["Renewal_Date"].dt.year

# حذف أي صف بدون شركة أو قسم أو سنة
clients = clients.dropna(subset=["Company", "Department", "Year"])

# =============================
#  Clean Finance Data
# =============================
finance.columns = finance.columns.str.strip()
finance["Year"] = finance["Year"].astype(int)

# =============================
#  1. Active Clients by Year
# =============================
clients_per_year = clients.groupby("Year")["Company"].nunique().reset_index(name="Active_Clients")
clients_per_year["Growth_%"] = (clients_per_year["Active_Clients"].pct_change() * 100).round(1)

fig1 = px.bar(
    clients_per_year, x="Year", y="Active_Clients", text="Active_Clients",
    title="Active Clients by Year", template="plotly_white",
    color_discrete_sequence=["#0077b6"]
)
fig1.update_traces(textposition="outside")
fig1.show()

# =============================
#  2. Renewal Frequency
# =============================
renewal_counts = clients.groupby("Company")["Renewal_No"].max().value_counts().sort_index().reset_index()
renewal_counts.columns = ["Renewal_Times", "Number_of_Clients"]

fig2 = px.bar(
    renewal_counts, x="Renewal_Times", y="Number_of_Clients",
    title="Distribution of Client Renewals", text="Number_of_Clients",
    template="plotly_white", color_discrete_sequence=["#00b4d8"]
)
fig2.update_traces(textposition="outside")
fig2.show()

# =============================
#  3. Market Share by Department (All Contracts)
# =============================
dept_share = clients.groupby("Department")["Company"].count().reset_index(name="Total_Contracts")
dept_share["Share_%"] = round(100 * dept_share["Total_Contracts"] / dept_share["Total_Contracts"].sum(), 1)

fig3 = px.pie(
    dept_share, names="Department", values="Total_Contracts",
    title="Market Concentration by Contract Count", hole=0.45, template="plotly_white"
)
fig3.update_traces(textinfo="label+percent", pull=[0.05]*len(dept_share))
fig3.show()

# =============================
#  4. First Contracts Only
# =============================
first_contracts = clients[clients["Renewal_No"] == 0]
first_share = first_contracts.groupby("Department")["Company"].count().reset_index(name="First_Contracts")
first_share["Share_%"] = round(100 * first_share["First_Contracts"] / first_share["First_Contracts"].sum(), 1)

fig4 = px.pie(
    first_share, names="Department", values="First_Contracts",
    title="Market Concentration by First Contracts Only",
    hole=0.45, template="plotly_white"
)
fig4.update_traces(textinfo="label+percent", pull=[0.05]*len(first_share))
fig4.show()

# =============================
#  5. Client Retention (Year-to-Year)
# =============================
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
fig5.show()

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

# ---- Version 2: Based on Unique Clients (excluding repeated renewals) ----
contracts_by_dept_unique = clients.groupby(["Department", "Year"])["Company"].nunique().reset_index(name="Unique_Clients")

merged_unique = pd.merge(contracts_by_dept_unique, finance, on=["Department", "Year"], how="left")

corr_sales_unique = merged_unique["Unique_Clients"].corr(merged_unique["Total Sales"])
corr_profit_unique = merged_unique["Unique_Clients"].corr(merged_unique["Total Profit"])

print("🔹 Correlation based on UNIQUE Clients (first contracts per client):")
print(f"   ↳ Clients vs Sales:  {corr_sales_unique:.2f}")
print(f"   ↳ Clients vs Profit: {corr_profit_unique:.2f}\n")

fig_corr3 = px.scatter(
    merged_unique, x="Unique_Clients", y="Total Sales", color="Department",
    trendline="ols", title="Correlation (Unique Clients) Between Clients and Total Sales",
    template="plotly_white", hover_data=["Year"]
)
fig_corr3.show()

fig_corr4 = px.scatter(
    merged_unique, x="Unique_Clients", y="Total Profit", color="Department",
    trendline="ols", title="Correlation (Unique Clients) Between Clients and Total Profit",
    template="plotly_white", hover_data=["Year"]
)
fig_corr4.show()

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

# =============================
#  9. Summary Overview
# =============================
summary = finance.groupby("Department")[["Total Sales", "Total Profit"]].sum().reset_index()
summary["Overall Margin_%"] = round((summary["Total Profit"] / summary["Total Sales"]) * 100, 1)
display(summary)

# =============================
#  10. Key Clients Contribution Estimate
# =============================

# 1️⃣ حساب عدد العقود لكل عميل
client_contracts = clients.groupby(["Department", "Company"])["Renewal_No"].max().reset_index()
client_contracts["Total_Contracts"] = client_contracts["Renewal_No"] + 1  # +1 عشان العقد الأصلي

# 2️⃣ دمج مع صافي الربح لكل قسم وسنة
# لو عايز تحسب لكل سنة:
merged_clients_profit = pd.merge(client_contracts, finance[["Department", "Year", "Total Profit"]], on="Department", how="left")

# 3️⃣ حساب نسبة العميل من مجموع العقود في القسم
dept_totals = client_contracts.groupby("Department")["Total_Contracts"].sum().reset_index(name="Dept_Total_Contracts")
merged_clients_profit = pd.merge(merged_clients_profit, dept_totals, on="Department", how="left")
merged_clients_profit["Contracts_Share_%"] = round(100 * merged_clients_profit["Total_Contracts"] / merged_clients_profit["Dept_Total_Contracts"], 1)

# 4️⃣ تقدير مساهمة العميل في صافي الربح
merged_clients_profit["Estimated_Profit"] = round(merged_clients_profit["Contracts_Share_%"] / 100 * merged_clients_profit["Total Profit"], 2)

# 5️⃣ ترتيب كل قسم حسب أهم العملاء
top_clients_per_dept = merged_clients_profit.sort_values(["Department", "Estimated_Profit"], ascending=[True, False])

display(top_clients_per_dept[["Department", "Company", "Total_Contracts", "Contracts_Share_%", "Estimated_Profit"]])

# =============================
#  11. Visualizing Key Clients Contribution
# =============================

import plotly.express as px

# نأخذ فقط الأعمدة المهمة
plot_data = top_clients_per_dept[["Department", "Company", "Estimated_Profit"]]

# رسم بياني: كل قسم كمجموعة، والعملاء على محور X، وربحهم المقدر على Y
fig_clients = px.bar(
    plot_data,
    x="Company",
    y="Estimated_Profit",
    color="Department",
    text="Estimated_Profit",
    title="Top Clients Contribution to Department Profit",
    labels={"Estimated_Profit": "Estimated Profit (EGP)", "Company": "Client"},
    template="plotly_white",
    height=600
)

fig_clients.update_traces(textposition="outside")
fig_clients.update_layout(
    xaxis_title="Client",
    yaxis_title="Estimated Contribution to Profit",
    xaxis_tickangle=-45,
    barmode="group",
    legend_title_text="Department",
    margin=dict(t=80, b=150)
)

fig_clients.show()

# =============================
#  13. Top 15 Clients per Department
# =============================

# نأخذ أهم 15 عميل لكل قسم بناءً على Estimated_Profit
top_clients_15 = top_clients_per_dept.groupby("Department").head(15).reset_index(drop=True)

# =============================
#  14. Stacked Bar: Top 15 Clients per Department
# =============================

fig_top15 = px.bar(
    top_clients_15.sort_values(["Department", "Estimated_Profit"], ascending=[True, False]),
    x="Department",
    y="Estimated_Profit",
    color="Company",
    text="Estimated_Profit",
    title="Top 15 Clients Contribution per Department",
    labels={"Estimated_Profit": "Estimated Profit (EGP)", "Department": "Department"},
    template="plotly_white",
    height=600
)

fig_top15.update_traces(textposition="inside")
fig_top15.update_layout(
    yaxis_title="Estimated Profit (EGP)",
    xaxis_title="Department",
    legend_title_text="Client",
    margin=dict(t=80, b=150)
)

fig_top15.show()


print("✅ Full Strategic & Financial Analysis Completed — No duplicates were removed, all contracts included.")
