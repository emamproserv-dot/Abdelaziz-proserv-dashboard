import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import gdown


# إعدادات الصفحة
st.set_page_config(
    page_title="لوحة تحليل نتائج الأعمال",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS مخصص
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #F8F9FA;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1565C0;
    }
    .metric-label {
        font-size: 1rem;
        color: #546E7A;
    }
</style>
""", unsafe_allow_html=True)

# دالة تحميل البيانات
@st.cache_data
def load_data(uploaded_file):
    df = pd.read_excel(uploaded_file)
    
    # تنظيف وإعداد البيانات
    df.columns = df.columns.str.strip()
    df.rename(columns={
        "Company Name": "Company",
        "Department": "Department",
        "Renewal Number": "Renewal_No",
        "Renewal Date": "Renewal_Date",
        "Contract Duration (Months)": "Duration_Months",
        "Cost": "Cost"
    }, inplace=True)
    
    df["Cost"] = df["Cost"].astype(str)
    df["Renewal_Date"] = pd.to_datetime(df["Renewal_Date"].astype(str) + "-01-01", errors="coerce")
    df["Year"] = df["Renewal_Date"].dt.year
    df = df.dropna(subset=["Company", "Year"])
    df["Numeric_Cost"] = pd.to_numeric(df["Cost"].str.replace("[^0-9.]", "", regex=True), errors="coerce")
    
    # استبعاد قسم Outsource من الحسابات المالية
    df_financial = df[df["Department"].str.lower() != "outsource"].copy()
    
    # إضافة نوع العقد (جديد أو تجديد)
    df["Contract_Type"] = df["Renewal_No"].apply(lambda x: "New" if x == 1 else "Renewal")
    
    return df, df_financial

# دالة تحويل DataFrame إلى Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()
# في دالة main() قبل تحميل الملف
if uploaded_file is None:
    st.sidebar.subheader("تحميل البيانات من Google Drive")
    file_url = st.sidebar.text_input(
        "رابط ملف Google Drive (مشاركة مع أي شخص لديه الرابط)",
        help="انسخ الرابط من Google Drive بعد مشاركة الملف"
    )
    
    if file_url:
        try:
            # تحويل رابط Google Drive إلى رابط تحميل مباشر
            file_id = file_url.split("/")[-2]
            download_url = f"https://drive.google.com/uc?id={file_id}"
            
            # تحميل الملف
            output = "data.xlsx"
            gdown.download(download_url, output, quiet=False)
            
            # قراءة الملف
            df, df_financial = load_data(output)
            st.sidebar.success("تم تحميل البيانات بنجاح!")
        except Exception as e:
            st.sidebar.error(f"خطأ في تحميل الملف: {e}")
            return
    else:
        st.info("يرجى رفع ملف Excel أو إدخال رابط Google Drive")
        return
        
# =============================
#  واجهة المستخدم
# =============================
def main():
    st.sidebar.header("الإعدادات والفلاتر")
    
    uploaded_file = st.sidebar.file_uploader(
        "ارفع ملف Excel", 
        type=["xlsx", "xls"],
        help="يرجى رفع ملف Excel يحتوي على بيانات العملاء"
    )
    
    if uploaded_file is not None:
        df, df_financial = load_data(uploaded_file)
        
        # الحصول على القيم الفريدة للفلاتر
        years = sorted(df["Year"].dropna().unique())
        companies = sorted(df["Company"].unique())
        departments = sorted(df["Department"].unique())
        
        # الفلاتر
        selected_years = st.sidebar.multiselect("اختر السنوات", options=years, default=years)
        selected_companies = st.sidebar.multiselect("اختر الشركات", options=companies, default=companies[:10])
        selected_departments = st.sidebar.multiselect("اختر الأقسام", options=departments, default=departments)
        
        # تطبيق الفلاتر
        filtered_df = df[
            (df["Year"].isin(selected_years)) &
            (df["Company"].isin(selected_companies)) &
            (df["Department"].isin(selected_departments))
        ]
        
        filtered_financial = df_financial[
            (df_financial["Year"].isin(selected_years)) &
            (df_financial["Company"].isin(selected_companies)) &
            (df_financial["Department"].isin(selected_departments))
        ]
        
        # =============================
        #  الرئيسية
        # =============================
        st.markdown("<h1 class='main-header'>لوحة تحليل نتائج الأعمال</h1>", unsafe_allow_html=True)
        
        # =============================
        #  نظرة عامة
        # =============================
        st.header("نظرة عامة")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_companies = filtered_df["Company"].nunique()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{total_companies}</div>
                <div class="metric-label">إجمالي الشركات</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            total_revenue = filtered_financial["Numeric_Cost"].sum()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{total_revenue:,.2f}</div>
                <div class="metric-label">إجمالي الإيرادات</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            avg_contract_value = filtered_financial["Numeric_Cost"].mean()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{avg_contract_value:,.2f}</div>
                <div class="metric-label">متوسط قيمة العقد</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            total_contracts = len(filtered_df)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{total_contracts}</div>
                <div class="metric-label">إجمالي العقود</div>
            </div>
            """, unsafe_allow_html=True)
        
        # =============================
        #  اتجاهات العملاء
        # =============================
        st.header("اتجاهات العملاء")
        
        # نمو العملاء
        client_growth = filtered_df.groupby("Year")["Company"].nunique().reset_index(name="Active_Clients")
        client_growth["Growth(%)"] = client_growth["Active_Clients"].pct_change() * 100
        
        fig1 = px.bar(
            client_growth, 
            x="Year", 
            y="Active_Clients", 
            title="نمو العملاء عبر السنوات", 
            text="Active_Clients", 
            template="plotly_white"
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        st.download_button(
            label="تحميل جدول نمو العملاء",
            data=to_excel(client_growth),
            file_name="customer_growth.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # =============================
        #  تحليل الإيرادات
        # =============================
        st.header("تحليل الإيرادات")
        
        # نمو الإيرادات
        revenue_growth = filtered_financial.groupby("Year")["Numeric_Cost"].sum().reset_index(name="Total_Cost")
        revenue_growth["Growth(%)"] = revenue_growth["Total_Cost"].pct_change() * 100
        
        fig2 = px.line(
            revenue_growth, 
            x="Year", 
            y="Total_Cost", 
            markers=True, 
            title="نمو حجم الأعمال عبر السنوات", 
            template="plotly_white"
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        st.download_button(
            label="تحميل جدول نمو الإيرادات",
            data=to_excel(revenue_growth),
            file_name="revenue_growth.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # =============================
        #  تحليل العقود
        # =============================
        st.header("تحليل العقود")
        
        # مقارنة العقود الجديدة والمجددة
        contract_type_counts = filtered_df["Contract_Type"].value_counts().reset_index()
        contract_type_counts.columns = ["Contract_Type", "Count"]
        
        fig3 = px.pie(
            contract_type_counts, 
            names="Contract_Type", 
            values="Count", 
            title="مقارنة بين العقود الجديدة والمجددة",
            template="plotly_white", 
            hole=0.3
        )
        st.plotly_chart(fig3, use_container_width=True)
        
        st.download_button(
            label="تحليل أنواع العقود",
            data=to_excel(contract_type_counts),
            file_name="contract_types.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # =============================
        #  توزيع الأقسام
        # =============================
        st.header("توزيع الأقسام")
        
        dept_distribution = filtered_df.groupby("Department")["Company"].nunique().reset_index(name="Unique_Clients")
        
        fig4 = px.bar(
            dept_distribution, 
            x="Department", 
            y="Unique_Clients",
            title="توزيع العملاء حسب القسم",
            text="Unique_Clients", 
            template="plotly_white"
        )
        fig4.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig4, use_container_width=True)
        
        st.download_button(
            label="تحميل توزيع الأقسام",
            data=to_excel(dept_distribution),
            file_name="department_distribution.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.markdown("---")
        st.markdown("تم تطوير لوحة التحكم بواسطة فريق تحليل البيانات")
    
    else:
        st.info("يرجى رفع ملف Excel لعرض لوحة التحكم")

if __name__ == "__main__":
    main()

