import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Set page title and layout
st.set_page_config(page_title="Customer Segmentation Dashboard", layout="wide")

# --- Title and Introduction ---
st.title("🛍️ E-commerce Customer Segmentation Dashboard")
st.markdown("This dashboard presents the results of an RFM-based customer segmentation analysis, identifying key customer personas and providing actionable insights.")
st.markdown("---")

# --- Load the cleaned data ---
# Uses caching to avoid reloading the file on every interaction
@st.cache_data
def load_data():
    """Loads and returns the cleaned RFM data."""
    try:
        df = pd.read_csv('rfm_data_cleaned.csv')
        # Ensure the Cluster column is string type for mapping
        df['Cluster'] = df['Cluster'].astype(str)
        return df
    except FileNotFoundError:
        st.error("Data file 'rfm_data_cleaned.csv' not found. Please run the Jupyter Notebook to generate it.")
        return None

rfm_df = load_data()

if rfm_df is not None:
    # --- Persona Naming (from your analysis) ---
    persona_names = {
        '3': 'High-Value Champions 🏆',
        '1': 'Loyal & Regular 🌟',
        '0': 'New & Promising 🌱',
        '2': 'Lapsed Customers 😴'
    }
    rfm_df['Persona'] = rfm_df['Cluster'].map(persona_names)

    # --- Sidebar Filters ---
    st.sidebar.header("Explore Segments")
    selected_personas = st.sidebar.multiselect(
        "Select Customer Personas",
        options=list(persona_names.values()),
        default=list(persona_names.values())
    )

    if not selected_personas:
        st.warning("Please select at least one persona.")
        st.stop()
    
    filtered_df = rfm_df[rfm_df['Persona'].isin(selected_personas)]

    # --- Dashboard Content ---
    st.header("Segment Breakdown & Key Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    # KPI 1: Total Customers
    with col1:
        total_customers = filtered_df['CustomerID'].nunique()
        st.metric("Total Customers in View", f"{total_customers:,}")

    # KPI 2: Total Revenue
    with col2:
        total_revenue = filtered_df['Monetary'].sum()
        st.metric("Total Revenue in View", f"${total_revenue:,.2f}")

    # KPI 3: Total Segments
    with col3:
        unique_segments = filtered_df['Persona'].nunique()
        st.metric("Selected Segments", unique_segments)

    # --- Segment Summary Table ---
    st.markdown("### Segment Summary Table")
    summary_table = filtered_df.groupby('Persona').agg(
        Avg_Recency_Days=('Recency', 'mean'),
        Avg_Frequency=('Frequency', 'mean'),
        Avg_Monetary=('Monetary', 'mean'),
        Customer_Count=('CustomerID', 'count')
    ).reset_index()

    summary_table['Avg_Recency_Days'] = summary_table['Avg_Recency_Days'].round(1)
    summary_table['Avg_Frequency'] = summary_table['Avg_Frequency'].round(1)
    summary_table['Avg_Monetary'] = summary_table['Avg_Monetary'].map('${:,.2f}'.format)
    summary_table['Customer_Percentage'] = (summary_table['Customer_Count'] / filtered_df['CustomerID'].nunique() * 100).round(1)
    
    st.dataframe(summary_table.sort_values(by='Customer_Count', ascending=False), use_container_width=True)
    
    # --- Visualizations ---
    st.markdown("### Segment Visualizations")
    
    tab1, tab2, tab3 = st.tabs(["Recency", "Frequency", "Monetary"])

    # Bar chart for Recency
    with tab1:
        fig_recency = px.bar(
            summary_table,
            x='Persona',
            y='Avg_Recency_Days',
            title='Average Recency by Persona (Lower is Better)',
            color='Persona', # Use the Persona name for coloring
            labels={'Avg_Recency_Days': 'Average Recency (Days)'}
        )
        # Manually invert the Y-axis for Recency since lower is better
        fig_recency.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_recency, use_container_width=True)

    # Bar chart for Frequency
    with tab2:
        fig_frequency = px.bar(
            summary_table,
            x='Persona',
            y='Avg_Frequency',
            title='Average Frequency by Persona',
            color='Persona', # Use the Persona name for coloring
            labels={'Avg_Frequency': 'Average Frequency (Purchases)'}
        )
        st.plotly_chart(fig_frequency, use_container_width=True)

    # Bar chart for Monetary
    with tab3:
        # Convert the formatted string back to float for plotting
        monetary_float = summary_table['Avg_Monetary'].str.replace('$', '').str.replace(',', '').astype(float)
        
        fig_monetary = px.bar(
            summary_table,
            x='Persona',
            y=monetary_float,
            title='Average Monetary by Persona',
            color='Persona', # Use the Persona name for coloring
            labels={'y': 'Average Monetary (Total Spent)'}
        )
        st.plotly_chart(fig_monetary, use_container_width=True)

    # Scatter plot of Frequency vs. Monetary
    st.markdown("### Scatter Plot of Segments")
    fig_scatter = px.scatter(
        filtered_df,
        x='Frequency_log',
        y='Monetary_log',
        color='Persona',
        hover_data=['Recency'],
        title="Segments on a Log-Transformed Plot",
        labels={'Frequency_log': 'Log(Frequency)', 'Monetary_log': 'Log(Monetary)'}
    )
    st.plotly_chart(fig_scatter, use_container_width=True)