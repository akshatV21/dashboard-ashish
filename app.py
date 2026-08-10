import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Executive Sales Performance Dashboard",
    page_icon="📊",
    layout="wide"
)

DATA_FILE = "shared_sales_data.csv"

# --- HELPER FUNCTIONS FOR SHARED STORAGE ---
def load_shared_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return None

def save_shared_data(df):
    df.to_csv(DATA_FILE, index=False)

# Initialize Session State
if "df" not in st.session_state:
    st.session_state["df"] = load_shared_data()

# --- HEADER SECTION ---
st.title("⚡ Executive Sales Performance Dashboard")
st.caption("Centralized Multi-User Sales Analytics Hub (View-Only for Team)")

# --- SIDEBAR & ROLE-BASED ACCESS CONTROL ---
with st.sidebar:
    st.header("📂 Data Management")
    
    # Mode selection
    access_mode = st.radio("Access Level", ["Viewer (Read-Only)", "Admin (Upload & Modify)"])
    
    if access_mode == "Admin (Upload & Modify)":
        # Ask for admin password
        admin_password = st.text_input("Enter Admin Password", type="password")
        
        # Set your secret password here (Change 'Admin123!' to your desired secure password)
        if admin_password == "Ash1985!":
            st.success("🔓 Admin access granted.")
            
            uploaded_file = st.file_uploader("Upload New Sales CSV", type=["csv"])
            if uploaded_file is not None:
                try:
                    new_df = pd.read_csv(uploaded_file)
                    col_map = {
                        'Branch': 'Branch Name', 'Outlet': 'Branch Name',
                        'Qty': 'Quantity', 'Net Sales': 'Net Amount',
                        'Gross': 'Gross Amount', 'Discount': 'Discounts'
                    }
                    new_df.rename(columns=col_map, inplace=True)
                    save_shared_data(new_df)
                    st.session_state["df"] = new_df
                    st.success("✅ Shared Database Updated for all viewers!")
                except Exception as e:
                    st.error(f"Error parsing CSV: {e}")

            if st.button("🔄 Reset Shared Data"):
                if os.path.exists(DATA_FILE):
                    os.remove(DATA_FILE)
                st.session_state["df"] = None
                st.rerun()
        elif admin_password != "":
            st.error("❌ Incorrect password.")
    else:
        st.info("👀 You are viewing in **Read-Only Mode**. Only the designated administrator can upload or reset data.")

df = st.session_state["df"]

if df is None:
    st.info("👈 No data available yet. An administrator must upload a POS Sales CSV to initialize the dashboard.")
    st.stop()

# --- MAIN DASHBOARD TABS ---
tab1, tab2, tab3 = st.tabs([
    "📈 Executive Summary & Charts", 
    "🌿 4-Level Hierarchical Drilldown", 
    "📦 Item Name → Outlet Quantity Matrix"
])

# ==========================================
# TAB 1: EXECUTIVE SUMMARY & CHARTS
# ==========================================
with tab1:
    st.subheader("High-Level KPIs")
    
    net_rev = df['Net Amount'].sum() if 'Net Amount' in df.columns else 0
    total_qty = df['Quantity'].sum() if 'Quantity' in df.columns else 0
    cogs = df['Materials Cost'].sum() if 'Materials Cost' in df.columns else 0
    cogs_pct = (cogs / net_rev * 100) if net_rev > 0 else 0
    margin_pct = 100 - cogs_pct

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Net Revenue", f"₹{net_rev:,.0f}")
    kpi2.metric("Units Sold", f"{total_qty:,.0f} units")
    kpi3.metric("Gross Margin %", f"{margin_pct:.1f}%")
    kpi4.metric("Food Cost %", f"{cogs_pct:.1f}%")

    st.markdown("---")
    
    col_chart1, col_chart2 = st.columns([2, 1])
    
    with col_chart1:
        st.subheader("Branch Net Revenue Comparison")
        if 'Branch Name' in df.columns and 'Net Amount' in df.columns:
            branch_df = df.groupby('Branch Name')['Net Amount'].sum().reset_index().sort_values(by='Net Amount', ascending=False)
            fig_branch = px.bar(branch_df, x='Branch Name', y='Net Amount', text_auto='.2s', color='Branch Name', color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig_branch, use_container_width=True)
            
    with col_chart2:
        st.subheader("Channel Mix")
        if 'Channel' in df.columns and 'Net Amount' in df.columns:
            channel_df = df.groupby('Channel')['Net Amount'].sum().reset_index()
            fig_channel = px.pie(channel_df, names='Channel', values='Net Amount', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_channel, use_container_width=True)

# ==========================================
# TAB 2: 4-LEVEL HIERARCHICAL DRILLDOWN
# ==========================================
with tab2:
    st.subheader("Hierarchy Drilldown: Outlet ➔ Channel ➔ Category ➔ Item")
    
    selected_outlet = st.selectbox("Select Store Outlet", ["All Outlets"] + sorted(df['Branch Name'].unique().tolist()))
    
    filtered_h_df = df if selected_outlet == "All Outlets" else df[df['Branch Name'] == selected_outlet]
    
    selected_channel = st.selectbox("Select Sales Channel", ["All Channels"] + sorted(filtered_h_df['Channel'].unique().tolist()))
    if selected_channel != "All Channels":
        filtered_h_df = filtered_h_df[filtered_h_df['Channel'] == selected_channel]
        
    selected_cat = st.selectbox("Select Category", ["All Categories"] + sorted(filtered_h_df['Category'].dropna().unique().tolist()))
    if selected_cat != "All Categories":
        filtered_h_df = filtered_h_df[filtered_h_df['Category'] == selected_cat]

    st.markdown("#### Item SKU Level Data Breakdown")
    summary_cols = ['Branch Name', 'Channel', 'Category', 'Item Group Name', 'Quantity', 'Net Amount']
    available_cols = [c for c in summary_cols if c in filtered_h_df.columns]
    
    st.dataframe(filtered_h_df[available_cols], use_container_width=True)

# ==========================================
# TAB 3: ITEM NAME -> OUTLET QUANTITY MATRIX
# ==========================================
with tab3:
    st.subheader("Item Sales Matrix across Outlets")
    
    f1, f2, f3 = st.columns(3)
    
    with f1:
        outlet_filter = st.selectbox("Filter Outlet Store", ["All Outlets"] + sorted(df['Branch Name'].unique().tolist()))
    with f2:
        item_filter = st.selectbox("Select Item Name", ["All Items"] + sorted(df['Item Group Name'].dropna().unique().tolist()))
    with f3:
        search_kw = st.text_input("Search Item/SKU", placeholder="e.g. Burrito, Nachos...")

    matrix_df = df.copy()
    if outlet_filter != "All Outlets":
        matrix_df = matrix_df[matrix_df['Branch Name'] == outlet_filter]
    if item_filter != "All Items":
        matrix_df = matrix_df[matrix_df['Item Group Name'] == item_filter]
    if search_kw:
        matrix_df = matrix_df[matrix_df['Item Group Name'].str.contains(search_kw, case=False, na=False)]

    pivot_matrix = matrix_df.pivot_table(
        index=['Item Group Name', 'Category'],
        columns='Branch Name',
        values=['Quantity', 'Net Amount'],
        aggfunc='sum',
        fill_value=0
    )
    
    st.dataframe(pivot_matrix, use_container_width=True)