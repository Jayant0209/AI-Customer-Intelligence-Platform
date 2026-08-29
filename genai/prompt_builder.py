from genai.business_metrics import get_business_metrics


def build_customer_insight_prompt(question):
    """
    Build a focused GenAI prompt using only the verified
    Snowflake metrics relevant to the user's question.
    """

    metrics = get_business_metrics()

    overall = metrics["overall"]
    segments = metrics["segments"]
    clusters = metrics["clusters"]
    highest_value_cluster = metrics["highest_value_cluster"]

    question_lower = question.lower().strip()

    segment_map = {
        segment["segment"].lower(): segment
        for segment in segments
    }

    at_risk = segment_map.get("at risk")
    loyal = segment_map.get("loyal customers")

    # =========================================================
    # Determine relevant data
    # =========================================================

    relevant_sections = []

    # Segment-related questions
    if any(
        keyword in question_lower
        for keyword in [
            "segment",
            "retention",
            "loyal",
            "risk",
            "loyalty",
            "churn",
            "engagement",
            "re-engagement",
            "reengagement",
        ]
    ):

        segment_text = "\n".join(
            [
                (
                    f"- {segment['segment']}: "
                    f"{segment['customer_count']} customers "
                    f"({segment['customer_percentage']}%), "
                    f"average recency {segment['avg_recency_days']} days, "
                    f"average frequency {segment['avg_frequency']}, "
                    f"average monetary value "
                    f"{segment['avg_monetary_value']:.2f}"
                )
                for segment in segments
            ]
        )

        relevant_sections.append(
            f"Customer Segments:\n{segment_text}"
        )

    # Cluster-related questions
    if any(
        keyword in question_lower
        for keyword in [
            "cluster",
            "upsell",
            "upselling",
        ]
    ):

        cluster_text = "\n".join(
            [
                (
                    f"- Cluster {cluster['cluster_id']}: "
                    f"{cluster['customer_count']} customers, "
                    f"average recency {cluster['avg_recency_days']} days, "
                    f"average frequency {cluster['avg_frequency']}, "
                    f"average monetary value "
                    f"{cluster['avg_monetary_value']:.2f}"
                )
                for cluster in clusters
            ]
        )

        relevant_sections.append(
            f"Customer Clusters:\n{cluster_text}"
        )

        if highest_value_cluster:

            relevant_sections.append(
                "Highest-Value Cluster:\n"
                f"- Cluster {highest_value_cluster['cluster_id']}: "
                f"average monetary value "
                f"{highest_value_cluster['avg_monetary_value']:.2f}"
            )

    # Overall customer-base questions
    if any(
        keyword in question_lower
        for keyword in [
            "overall",
            "customer base",
            "summary",
            "summarize",
            "business",
        ]
    ):

        relevant_sections.append(
            "Overall Customer Metrics:\n"
            f"- Total customers: {overall['total_customers']}\n"
            f"- Total monetary value: "
            f"{overall['total_monetary_value']:.2f}\n"
            f"- Average recency: "
            f"{overall['avg_recency_days']} days\n"
            f"- Average frequency: "
            f"{overall['avg_frequency']}"
        )

    # If no specific category was detected, provide overall context
    # instead of sending every available metric.
    if not relevant_sections:

        relevant_sections.append(
            "Overall Customer Metrics:\n"
            f"- Total customers: {overall['total_customers']}\n"
            f"- Average recency: "
            f"{overall['avg_recency_days']} days\n"
            f"- Average frequency: "
            f"{overall['avg_frequency']}"
        )

    verified_data = "\n\n".join(relevant_sections)

    # =========================================================
    # GenAI prompt
    # =========================================================

    prompt = f"""
You are an AI Customer Intelligence Analyst.

Answer the user's business question using ONLY the verified
customer data provided below.

IMPORTANT RULES:

- Use only the verified data.
- Never invent numerical values.
- Never modify numerical values.
- Never create unsupported statistics.
- Answer the question directly.
- Do not introduce unrelated information.
- Separate factual findings from recommendations.
- Recommendations must be supported by the provided data.
- Do not provide numerical business impact estimates.
- If the data is insufficient to answer the question,
  clearly say that the available data is insufficient.
- Use concise professional business language.
- Complete all three sections.
- Keep the response below 100 words.

VERIFIED CUSTOMER DATA

{verified_data}

USER QUESTION:

{question}

RESPONSE FORMAT:

Key Findings:
- Finding 1
- Finding 2

Recommended Actions:
- Action 1
- Action 2

Potential Business Impact:
Explain the likely qualitative business impact in 1 sentence.
"""

    return prompt.strip()
