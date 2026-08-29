import os
import sys

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import pandas as pd
import plotly.express as px

from datetime import datetime
from genai.business_metrics import get_business_metrics
from streamlit_app.snowflake_connection import get_snowflake_connection
from genai.insight_engine import generate_customer_insight

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Customer Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main {
        background-color: #f8fafc;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    .dashboard-title {
        font-size: 2.4rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .dashboard-subtitle {
        color: #64748b;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }

    .kpi-card {
        width: 100%;
        min-height: 135px;
        box-sizing: border-box;

        background: white;
        padding: 1.25rem;
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);

        overflow: hidden;
    }

    .kpi-title {
        color: #64748b;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .kpi-value {
        color: #0f172a;
        font-size: clamp(1.35rem, 2vw, 1.8rem);
        font-weight: 700;
        margin-top: 0.25rem;
        line-height: 1.2;

        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .section-title {
        font-size: 1.35rem;
        font-weight: 650;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="dashboard-title">🤖 AI Customer Intelligence Platform</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="dashboard-subtitle">'
    "RFM-based customer segmentation powered by Snowflake, Airflow and Machine Learning"
    "</div>",
    unsafe_allow_html=True,
)


# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data(ttl=300)
def load_customer_segments():

    conn = get_snowflake_connection()

    query = """
        SELECT
            CUSTOMER_ID,
            FIRST_NAME,
            LAST_NAME,
            EMAIL,
            CITY,
            STATE,
            CUSTOMER_SEGMENT,
            RECENCY_DAYS,
            FREQUENCY,
            MONETARY_VALUE,
            FIRST_ORDER_DATE,
            LAST_ORDER_DATE,
            RECENCY_SCORE,
            FREQUENCY_SCORE,
            MONETARY_SCORE,
            RFM_SCORE,
            RFM_TOTAL_SCORE,
            CLUSTER_ID,
            SEGMENT_NAME
        FROM AI_CUSTOMER_DB.ANALYTICS.CUSTOMER_SEGMENTS
    """

    try:
        df = pd.read_sql(query, conn)
    finally:
        conn.close()

    return df


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("⚙️ Dashboard Controls")

    if st.button(
        "🔄 Refresh Data",
        use_container_width=True,
    ):
        st.cache_data.clear()
        st.rerun()

    st.divider()

    st.markdown("### Filters")


# =========================================================
# LOAD
# =========================================================

try:

    df = load_customer_segments()

except Exception as e:

    st.error(
        "Unable to load customer segmentation data from Snowflake."
    )

    st.exception(e)

    st.stop()


if df.empty:

    st.warning(
        "No customer segmentation data is available."
    )

    st.stop()


# =========================================================
# FILTERS
# =========================================================

with st.sidebar:

    # ---------------------------------------------------------
    # CUSTOMER SEGMENT FILTER
    # ---------------------------------------------------------

    segment_options = sorted(
        df["SEGMENT_NAME"]
        .dropna()
        .unique()
        .tolist()
    )

    if "selected_segments" not in st.session_state:
        st.session_state.selected_segments = segment_options.copy()

    selected_segments = st.multiselect(
        "Customer Segment",
        options=segment_options,
        default=st.session_state.selected_segments,
        key="selected_segments",
    )

    # ---------------------------------------------------------
    # CLUSTER FILTER
    # ---------------------------------------------------------

    cluster_options = sorted(
        df["CLUSTER_ID"]
        .dropna()
        .unique()
        .tolist()
    )

    if "selected_clusters" not in st.session_state:
        st.session_state.selected_clusters = cluster_options.copy()

    selected_clusters = st.multiselect(
        "Cluster",
        options=cluster_options,
        default=st.session_state.selected_clusters,
        key="selected_clusters",
    )


# ---------------------------------------------------------
# APPLY FILTERS
# ---------------------------------------------------------

filtered_df = df[
    df["SEGMENT_NAME"].isin(selected_segments)
    & df["CLUSTER_ID"].isin(selected_clusters)
].copy()

# =========================================================
# KPI CALCULATIONS
# =========================================================

total_customers = len(filtered_df)

loyal_customers = len(
    filtered_df[
        filtered_df["SEGMENT_NAME"] == "Loyal Customers"
    ]
)

at_risk_customers = len(
    filtered_df[
        filtered_df["SEGMENT_NAME"] == "At Risk"
    ]
)

total_monetary = filtered_df["MONETARY_VALUE"].sum()

avg_monetary = (
    filtered_df["MONETARY_VALUE"].mean()
    if total_customers
    else 0
)

avg_frequency = (
    filtered_df["FREQUENCY"].mean()
    if total_customers
    else 0
)

avg_recency = (
    filtered_df["RECENCY_DAYS"].mean()
    if total_customers
    else 0
)


# =========================================================
# KPI CARDS
# =========================================================

st.markdown(
    '<div class="section-title">📈 Customer Overview</div>',
    unsafe_allow_html=True,
)

col1, col2, col3, col4 = st.columns(4)


def kpi_card(column, title, value):

    column.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


kpi_card(
    col1,
    "Total Customers",
    f"{total_customers:,}",
)

kpi_card(
    col2,
    "Loyal Customers",
    f"{loyal_customers:,}",
)

kpi_card(
    col3,
    "At Risk Customers",
    f"{at_risk_customers:,}",
)

def format_value(value):
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"{value / 1_000:.2f}K"
    return f"{value:,.0f}"


kpi_card(
    col4,
    "Total Customer Value",
    f"₹{format_value(total_monetary)}",
)

# =========================================================
# SECONDARY METRICS
# =========================================================

st.markdown(
    '<div class="section-title">📊 Customer Behavior Metrics</div>',
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)

col1.metric(
    "Average Monetary Value",
    f"{avg_monetary:,.0f}",
)

col2.metric(
    "Average Frequency",
    f"{avg_frequency:.2f}",
)

col3.metric(
    "Average Recency",
    f"{avg_recency:.2f} days",
)


# =========================================================
# SEGMENT ANALYSIS
# =========================================================

st.markdown(
    '<div class="section-title">🎯 Customer Segment Analysis</div>',
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)


segment_distribution = (
    filtered_df["SEGMENT_NAME"]
    .value_counts()
    .rename_axis("SEGMENT_NAME")
    .reset_index(name="CUSTOMER_COUNT")
)


with col1:

    st.subheader("Customer Distribution")

    fig_segment = px.bar(
        segment_distribution,
        x="SEGMENT_NAME",
        y="CUSTOMER_COUNT",
        text="CUSTOMER_COUNT",
        title="Customers by Segment",
    )

    fig_segment.update_layout(
        xaxis_title="Customer Segment",
        yaxis_title="Number of Customers",
        showlegend=False,
    )

    st.plotly_chart(
        fig_segment,
        use_container_width=True,
    )

with col2:

    st.subheader("Segment Summary")

    segment_summary = (
        filtered_df
        .groupby("SEGMENT_NAME")
        .agg(
            CUSTOMER_COUNT=("CUSTOMER_ID", "count"),
            AVG_RECENCY=("RECENCY_DAYS", "mean"),
            AVG_FREQUENCY=("FREQUENCY", "mean"),
            AVG_MONETARY=("MONETARY_VALUE", "mean"),
        )
        .reset_index()
    )

    segment_summary[
        [
            "AVG_RECENCY",
            "AVG_FREQUENCY",
            "AVG_MONETARY",
        ]
    ] = segment_summary[
        [
            "AVG_RECENCY",
            "AVG_FREQUENCY",
            "AVG_MONETARY",
        ]
    ].round(2)

    st.dataframe(
        segment_summary,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# CLUSTER ANALYSIS
# =========================================================

st.markdown(
    '<div class="section-title">🔬 ML Cluster Analysis</div>',
    unsafe_allow_html=True,
)

cluster_summary = (
    filtered_df
    .groupby("CLUSTER_ID")
    .agg(
        CUSTOMER_COUNT=("CUSTOMER_ID", "count"),
        AVG_RECENCY=("RECENCY_DAYS", "mean"),
        AVG_FREQUENCY=("FREQUENCY", "mean"),
        AVG_MONETARY=("MONETARY_VALUE", "mean"),
    )
    .reset_index()
)

cluster_summary[
    [
        "AVG_RECENCY",
        "AVG_FREQUENCY",
        "AVG_MONETARY",
    ]
] = cluster_summary[
    [
        "AVG_RECENCY",
        "AVG_FREQUENCY",
        "AVG_MONETARY",
    ]
].round(2)


col1, col2 = st.columns(2)

with col1:

    st.subheader("Customers by Cluster")

    fig_cluster = px.bar(
        cluster_summary,
        x="CLUSTER_ID",
        y="CUSTOMER_COUNT",
        text="CUSTOMER_COUNT",
        title="Customer Distribution by ML Cluster",
    )

    fig_cluster.update_layout(
        xaxis_title="Cluster ID",
        yaxis_title="Number of Customers",
        showlegend=False,
    )

    st.plotly_chart(
        fig_cluster,
        use_container_width=True,
    )

with col2:

    st.subheader("Cluster Metrics")

    st.dataframe(
        cluster_summary,
        use_container_width=True,
        hide_index=True,
    )

# =========================================================
# RFM BEHAVIOR ANALYSIS
# =========================================================

st.markdown(
    '<div class="section-title">📊 RFM Behavior Analysis</div>',
    unsafe_allow_html=True,
)

rfm_chart_df = (
    filtered_df
    .groupby("SEGMENT_NAME")
    .agg(
        AVG_RECENCY=("RECENCY_DAYS", "mean"),
        AVG_FREQUENCY=("FREQUENCY", "mean"),
        AVG_MONETARY=("MONETARY_VALUE", "mean"),
    )
    .reset_index()
)

fig_rfm = px.scatter(
    rfm_chart_df,
    x="AVG_RECENCY",
    y="AVG_FREQUENCY",
    size="AVG_MONETARY",
    text="SEGMENT_NAME",
    title="Customer Segment RFM Behavior",
)

fig_rfm.update_traces(
    textposition="top center"
)

fig_rfm.update_layout(
    xaxis_title="Average Recency (Days)",
    yaxis_title="Average Purchase Frequency",
)

st.plotly_chart(
    fig_rfm,
    use_container_width=True,
)

# =========================================================
# TOP CUSTOMERS
# =========================================================

st.markdown(
    '<div class="section-title">💰 Top Customers by Monetary Value</div>',
    unsafe_allow_html=True,
)

top_customers = (
    filtered_df
    .sort_values(
        "MONETARY_VALUE",
        ascending=False,
    )
    .head(10)
)

st.dataframe(
    top_customers[
        [
            "CUSTOMER_ID",
            "FIRST_NAME",
            "LAST_NAME",
            "CITY",
            "CUSTOMER_SEGMENT",
            "RECENCY_DAYS",
            "FREQUENCY",
            "MONETARY_VALUE",
            "CLUSTER_ID",
            "SEGMENT_NAME",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)


# =========================================================
# CUSTOMER SEARCH
# =========================================================

st.markdown(
    '<div class="section-title">🔎 Customer Explorer</div>',
    unsafe_allow_html=True,
)

search_id = st.text_input(
    "Search Customer ID",
    placeholder="Example: C009722",
)


if search_id:

    result = df[
        df["CUSTOMER_ID"]
        .astype(str)
        .str.contains(
            search_id,
            case=False,
            na=False,
        )
    ]

    if result.empty:

        st.warning(
            "No customer found."
        )

    else:

        st.dataframe(
            result,
            use_container_width=True,
            hide_index=True,
        )

# =========================================================
# AI EXECUTIVE SUMMARY
# =========================================================

st.markdown(
    '<div class="section-title">📊 AI Executive Summary</div>',
    unsafe_allow_html=True,
)

st.markdown(
    "A quick overview of the most important customer intelligence "
    "signals identified from the verified Snowflake data."
)

try:

    executive_metrics = get_business_metrics()

    exec_segments = executive_metrics["segments"]
    exec_clusters = executive_metrics["clusters"]

    exec_segment_map = {
        segment["segment"].lower(): segment
        for segment in exec_segments
    }

    exec_at_risk = exec_segment_map.get("at risk")
    exec_loyal = exec_segment_map.get("loyal customers")

    # Find highest-value cluster
    exec_highest_value_cluster = max(
        exec_clusters,
        key=lambda x: x["avg_monetary_value"],
    )

    # Find most engaged cluster based on lowest recency
    exec_most_engaged_cluster = min(
        exec_clusters,
        key=lambda x: x["avg_recency_days"],
    )

    # ---------------------------------------------------------
    # Executive Summary Cards
    # ---------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "🔴 At Risk Customers",
            f"{exec_at_risk['customer_count']:,}",
            f"{exec_at_risk['customer_percentage']}%",
        )

    with col2:

        st.metric(
            "💰 Highest-Value Cluster",
            f"Cluster {exec_highest_value_cluster['cluster_id']}",
            f"{exec_highest_value_cluster['avg_monetary_value']:,.2f}",
        )

    with col3:

        st.metric(
            "📈 Most Engaged Cluster",
            f"Cluster {exec_most_engaged_cluster['cluster_id']}",
            f"{exec_most_engaged_cluster['avg_recency_days']} days",
        )

    with col4:

        st.metric(
            "⭐ Loyal Customers",
            f"{exec_loyal['customer_count']:,}",
            f"{exec_loyal['customer_percentage']}%",
        )

    # ---------------------------------------------------------
    # Business Priorities
    # ---------------------------------------------------------

    st.markdown("### 🎯 Business Priorities")

    priority_col1, priority_col2 = st.columns(2)

    with priority_col1:

        st.markdown(
            f"""
            **🔴 Retention Priority**

            Focus retention campaigns on the **At Risk** segment,
            which contains **{exec_at_risk['customer_count']:,} customers**
            and has an average recency of
            **{exec_at_risk['avg_recency_days']} days**.
            """
        )

    with priority_col2:

        st.markdown(
            f"""
            **💰 Growth Priority**

            Focus high-value retention and upselling strategies on
            **Cluster {exec_highest_value_cluster['cluster_id']}**,
            which has the highest average monetary value of
            **{exec_highest_value_cluster['avg_monetary_value']:,.2f}**.
            """
        )

except Exception as e:

    st.warning(
        "Unable to generate the AI Executive Summary."
    )

    st.caption(
        f"Details: {e}"
    )

# =========================================================
# AI BUSINESS INSIGHTS
# =========================================================

st.markdown(
    '<div class="section-title">🧠 AI Business Insights</div>',
    unsafe_allow_html=True,
)

st.markdown(
    "Ask a business question about your customer data and get "
    "data-driven recommendations powered by the GenAI insight engine."
)

# ---------------------------------------------------------
# Suggested business questions
# ---------------------------------------------------------

suggested_questions = [
    "Which customer segment should we target for retention?",
    "Which cluster has the highest customer value?",
    "Why are customers At Risk?",
    "What can we do to improve customer loyalty?",
    "Which customers need immediate attention?",
    "Which customers are most valuable?",
    "Which customers are most engaged?",
    "Which customers are showing signs of churn?",
    "Which segment has the most customers?",
    "Which segment has the highest monetary value?",
    "Which segment has the highest purchase frequency?",
    "Which segment has the best recency?",
    "Where should we focus re-engagement campaigns?",
    "Give me a summary of the customer base.",
    "Custom question",
]

selected_question = st.selectbox(
    "Business Question",
    suggested_questions,
    index=0,
)

# ---------------------------------------------------------
# Custom question
# ---------------------------------------------------------

if selected_question == "Custom question":

    ai_question = st.text_input(
        "Enter your question",
        placeholder=(
            "Example: Which customers should we focus on for "
            "retention?"
        ),
    )

else:

    ai_question = selected_question


# ---------------------------------------------------------
# Generate Insight
# ---------------------------------------------------------

if st.button(
    "✨ Generate AI Insight",
    use_container_width=False,
):

    if not ai_question.strip():

        st.warning(
            "Please enter a business question."
        )

    else:

        with st.spinner(
            "Analyzing verified customer data..."
        ):

            try:

                insight = generate_customer_insight(
                    ai_question.strip()
                )

                # -------------------------------------------------
                # Key Findings
                # -------------------------------------------------

                st.markdown(
                    "### 🔍 Key Findings"
                )

                findings = insight.get(
                    "key_findings",
                    [],
                )

                if findings:

                    for finding in findings:

                        st.markdown(
                            f"- {finding}"
                        )

                else:

                    st.info(
                        "No key findings were generated."
                    )

                # -------------------------------------------------
                # Recommended Actions
                # -------------------------------------------------

                st.markdown(
                    "### 🎯 Recommended Actions"
                )

                actions = insight.get(
                    "recommended_actions",
                    [],
                )

                if actions:

                    for action in actions:

                        st.markdown(
                            f"- {action}"
                        )

                else:

                    st.info(
                        "No recommended actions were generated."
                    )

                # -------------------------------------------------
                # Business Impact
                # -------------------------------------------------

                st.markdown(
                    "### 📈 Potential Business Impact"
                )

                impact = insight.get(
                    "potential_business_impact",
                    "No business impact was generated.",
                )

                st.info(
                    impact
                )

                # -------------------------------------------------
                # Data Source
                # -------------------------------------------------

                st.caption(
                    f"📊 Data Source: "
                    f"{insight.get('source', 'Unknown')}"
                )

            except RuntimeError as e:

                st.warning(
                    "The local GenAI model is taking too long to "
                    "respond. The analytical engine is still "
                    "available for supported questions."
                )

                st.caption(
                    f"Details: {e}"
                )

            except Exception as e:

                st.error(
                    "Unable to generate the AI insight."
                )

                st.exception(e)

# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    f"Data source: AI_CUSTOMER_DB.ANALYTICS.CUSTOMER_SEGMENTS "
    f"| Records loaded: {len(df):,} "
    f"| Refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
