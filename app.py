import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- PAGE CONFIGURATION & CSS ---
st.set_page_config(
    page_title="Executive Sales Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom minimalistic styling
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        h1, h2, h3 { font-weight: 400 !important; }
        .st-emotion-cache-16txtl3 { padding: 2rem 1.5rem; }
    </style>
""", unsafe_allow_html=True)

DATA_FILE = "shared_sales_data.csv"

# --- HELPER FUNCTIONS ---
@st.cache_data(show_spinner=False)
def load_shared_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return None

def save_shared_data(df):
    df.to_csv(DATA_FILE, index=False)
    st.cache_data.clear()

# Initialize Session State
if "df" not in st.session_state:
    st.session_state["df"] = load_shared_data()

# --- SIDEBAR: ACCESS CONTROL ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=60) # Placeholder logo
    st.title("Data Portal")
    st.markdown("---")
    
    access_mode = st.radio("🔒 Access Level", ["Viewer (Read-Only)", "Admin (Manage Data)"])
    
    if access_mode == "Admin (Manage Data)":
        admin_password = st.text_input("Enter Admin Password", type="password", placeholder="Password...")
        
        if admin_password == "nybc2018":
            st.success("Admin unlocked")
            
            with st.expander("⬆️ Upload New Data", expanded=True):
                uploaded_file = st.file_uploader("Upload Sales CSV", type=["csv"], label_visibility="collapsed")
                
                if uploaded_file is not None:
                    try:
                        new_df = pd.read_csv(uploaded_file)
                        col_map = {
                            'Branch': 'Branch Name', 'Outlet': 'Branch Name',
                            'Qty': 'Quantity', 'Net Sales': 'Net Amount',
                            'Gross': 'Gross Amount', 'Discount': 'Discounts'
                        }
                        new_df.rename(columns=col_map, inplace=True)
                        new_df['Source File'] = uploaded_file.name
                        
                        if st.session_state["df"] is not None and not st.session_state["df"].empty:
                            existing_df = st.session_state["df"]
                            existing_df = existing_df[existing_df['Source File'] != uploaded_file.name]
                            updated_df = pd.concat([existing_df, new_df], ignore_index=True)
                        else:
                            updated_df = new_df
                            
                        save_shared_data(updated_df)
                        st.session_state["df"] = updated_df
                        st.toast(f"Data from {uploaded_file.name} saved!", icon="✅")
                    except Exception as e:
                        st.error(f"Upload failed: {e}")

            if st.button("🚨 Wipe All Database", type="primary", use_container_width=True):
                if os.path.exists(DATA_FILE):
                    os.remove(DATA_FILE)
                st.session_state["df"] = None
                st.cache_data.clear()
                st.rerun()
                
        elif admin_password != "":
            st.error("Incorrect password")
    else:
        st.info("You are in **Read-Only Mode**. Switch to Admin to upload data.")

df = st.session_state["df"]

# --- EMPTY STATE UI ---
if df is None or df.empty:
    st.title("⚡ Executive Sales Performance Dashboard")
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("")
        st.write("")
        st.info("👋 **Welcome to the Centralized Hub!**\n\nThe database is currently empty. An administrator needs to upload a POS Sales CSV using the sidebar on the left to initialize the dashboard.")
    st.stop()

# --- MAIN DASHBOARD ---
st.title("⚡ Executive Sales Performance")
st.caption(f"Currently analyzing {len(df):,} rows of data across {df['Source File'].nunique()} source files.")
st.markdown("---")

tab1, tab2, tab3 = st.tabs([
    "📊 Executive Summary", 
    "🌿 Deep Drilldown", 
    "🔥 Outlet Matrix (Heatmap)"
])

# ==========================================
# TAB 1: EXECUTIVE SUMMARY
# ==========================================
with tab1:
    st.markdown("#### High-Level Performance")
    
    # Get unique source files
    unique_files = sorted(df['Source File'].dropna().unique().tolist()) if 'Source File' in df.columns else []
    
    # Create sub-tabs: 1 for Combined, then 1 for each individual file
    sub_tab_names = ["🌍 All Files Combined"] + [f"📄 {f}" for f in unique_files]
    sub_tabs = st.tabs(sub_tab_names)
    
    # Map dataframes to their respective tabs
    file_dfs = [df] + [df[df['Source File'] == f] for f in unique_files]
    
    for i, current_tab in enumerate(sub_tabs):
        with current_tab:
            current_df = file_dfs[i]
            
            # --- KPIs ---
            net_rev = current_df['Net Amount'].sum() if 'Net Amount' in current_df.columns else 0
            total_qty = current_df['Quantity'].sum() if 'Quantity' in current_df.columns else 0
            cogs = current_df['Materials Cost'].sum() if 'Materials Cost' in current_df.columns else 0
            margin_pct = 100 - ((cogs / net_rev * 100) if net_rev > 0 else 0)

            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            with kpi1:
                st.metric("Net Revenue", f"₹{net_rev:,.0f}")
            with kpi2:
                st.metric("Units Sold", f"{total_qty:,.0f}")
            with kpi3:
                st.metric("Gross Margin", f"{margin_pct:.1f}%")
            with kpi4:
                file_count = current_df['Source File'].nunique() if 'Source File' in current_df.columns else 0
                st.metric("Files Included", file_count)
            
            st.write("")
            
            # --- CHARTS ---
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown("##### 🏢 Revenue by Branch")
                if 'Branch Name' in current_df.columns and 'Net Amount' in current_df.columns:
                    branch_df = current_df.groupby('Branch Name')['Net Amount'].sum().reset_index().sort_values(by='Net Amount', ascending=True)
                    if not branch_df.empty:
                        fig_branch = px.bar(branch_df, y='Branch Name', x='Net Amount', orientation='h', text_auto='.3s', color_discrete_sequence=['#4F8BF9'])
                        fig_branch.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", xaxis=dict(showgrid=False, zeroline=False), yaxis=dict(showgrid=False))
                        fig_branch.update_traces(hovertemplate='<b>%{y}</b><br>Revenue: ₹%{x:,.0f}<extra></extra>')
                        st.plotly_chart(fig_branch, use_container_width=True)
                    else:
                        st.info("No branch data available in this file.")
                    
            with c2:
                st.markdown("##### 🛍️ Channel Mix")
                if 'Channel' in current_df.columns and 'Net Amount' in current_df.columns:
                    channel_df = current_df.groupby('Channel')['Net Amount'].sum().reset_index()
                    if not channel_df.empty:
                        fig_channel = px.pie(channel_df, names='Channel', values='Net Amount', hole=0.55)
                        fig_channel.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=20, b=20, l=20, r=20))
                        st.plotly_chart(fig_channel, use_container_width=True)
                    else:
                        st.info("No channel data available in this file.")

# ==========================================
# TAB 2: 4-LEVEL HIERARCHICAL DRILLDOWN
# ==========================================
with tab2:
    st.markdown("#### 🌿 Hierarchy Drilldown")
    st.caption("Compare SKU performance side-by-side across your uploaded files.")
    
    f_col1, f_col2, f_col3 = st.columns(3)
    
    with f_col1:
        selected_outlet = st.selectbox("1. Outlet", ["All"] + sorted(df['Branch Name'].dropna().unique().tolist()))
    
    filtered_h_df = df if selected_outlet == "All" else df[df['Branch Name'] == selected_outlet]
    
    with f_col2:
        chan_options = ["All"] + sorted(filtered_h_df['Channel'].dropna().unique().tolist()) if 'Channel' in filtered_h_df.columns else ["All"]
        selected_channel = st.selectbox("2. Channel", chan_options)
        if selected_channel != "All":
            filtered_h_df = filtered_h_df[filtered_h_df['Channel'] == selected_channel]
            
    with f_col3:
        cat_options = ["All"] + sorted(filtered_h_df['Category'].dropna().unique().tolist()) if 'Category' in filtered_h_df.columns else ["All"]
        selected_cat = st.selectbox("3. Category", cat_options)
        if selected_cat != "All":
            filtered_h_df = filtered_h_df[filtered_h_df['Category'] == selected_cat]

    index_cols = ['Branch Name', 'Channel', 'Category', 'Item Group Name']
    available_index_cols = [c for c in index_cols if c in filtered_h_df.columns]
    
    if 'Source File' in filtered_h_df.columns and available_index_cols:
        try:
            pivoted_h_df = filtered_h_df.pivot_table(
                index=available_index_cols,
                columns='Source File',
                values=['Quantity', 'Net Amount'],
                aggfunc='sum',
                fill_value=0
            )
            
            styled_h_df = pivoted_h_df.style.format(precision=0, thousands=",")
            st.dataframe(styled_h_df, use_container_width=True, height=500)
        except Exception:
            st.dataframe(filtered_h_df.style.format(precision=0, thousands=","), use_container_width=True)
    else:
        st.dataframe(filtered_h_df, use_container_width=True)

# ==========================================
# TAB 3: MATRIX & HEATMAP
# ==========================================
with tab3:
    st.markdown("#### 🔥 Cross-Outlet Heatmap")
    st.caption("Spot your best selling items and locations instantly.")
    
    m_col1, m_col2, m_col3 = st.columns(3)
    
    with m_col1:
        outlet_filter = st.selectbox("Filter Outlet", ["All"] + sorted(df['Branch Name'].dropna().unique().tolist()), key='tab3_outlet')
    with m_col2:
        item_filter = st.selectbox("Filter Item Name", ["All"] + sorted(df['Item Group Name'].dropna().unique().tolist()), key='tab3_item')
    with m_col3:
        search_kw = st.text_input("🔍 Search Item", placeholder="e.g. Burger, Nachos...")

    matrix_df = df.copy()
    if outlet_filter != "All":
        matrix_df = matrix_df[matrix_df['Branch Name'] == outlet_filter]
    if item_filter != "All":
        matrix_df = matrix_df[matrix_df['Item Group Name'] == item_filter]
    if search_kw:
        matrix_df = matrix_df[matrix_df['Item Group Name'].str.contains(search_kw, case=False, na=False)]

    if not matrix_df.empty:
        pivot_matrix = matrix_df.pivot_table(
            index=['Category', 'Item Group Name'],
            columns='Branch Name',
            values='Net Amount',
            aggfunc='sum',
            fill_value=0
        )
        
        styled_matrix = pivot_matrix.style.background_gradient(cmap='Blues', axis=1).format("₹{:,.0f}")
        st.dataframe(styled_matrix, use_container_width=True, height=600)
    else:
        st.warning("No items match your search criteria.")