from genai.business_metrics import get_business_metrics
from genai.prompt_builder import build_customer_insight_prompt
from genai.ollama_client import generate_insight


def _build_response(question, findings, actions, impact):
    return {
        "question": question,
        "key_findings": findings,
        "recommended_actions": actions,
        "potential_business_impact": impact,
        "source": "Snowflake CUSTOMER_SEGMENTS",
    }


def _generate_dynamic_insight(question):
    """
    Dynamic GenAI fallback.

    Uses verified Snowflake metrics as context and Ollama only
    when the question does not match a deterministic analytical
    pattern.
    """

    prompt = build_customer_insight_prompt(question)

    response = generate_insight(prompt)

    return {
        "question": question,
        "key_findings": [response],
        "recommended_actions": [],
        "potential_business_impact": (
            "Insight generated using verified Snowflake customer "
            "metrics and the local Ollama model."
        ),
        "source": "Snowflake CUSTOMER_SEGMENTS + Ollama",
    }


def generate_customer_insight(question):

    metrics = get_business_metrics()

    overall = metrics["overall"]
    segments = metrics["segments"]
    clusters = metrics["clusters"]
    highest_value_cluster = metrics["highest_value_cluster"]

    question_lower = question.lower().strip()

    # =========================================================
    # SEGMENT LOOKUP
    # =========================================================

    segment_map = {
        segment["segment"].lower(): segment
        for segment in segments
    }

    at_risk = segment_map.get("at risk")
    loyal = segment_map.get("loyal customers")

    # =========================================================
    # 1. RETENTION TARGETING
    # =========================================================

    if (
        "retention" in question_lower
        or (
            "target" in question_lower
            and "segment" in question_lower
        )
    ):

        if at_risk and loyal:

            findings = [
                (
                    f"At Risk customers represent "
                    f"{at_risk['customer_count']} customers "
                    f"({at_risk['customer_percentage']}%) of the customer base."
                ),
                (
                    f"At Risk customers have higher average recency "
                    f"({at_risk['avg_recency_days']} days) and lower average "
                    f"frequency ({at_risk['avg_frequency']}) than Loyal Customers."
                ),
            ]

            actions = [
                "Prioritize the At Risk segment for retention campaigns.",
                "Use personalized re-engagement offers and reminders to encourage repeat purchases.",
            ]

            impact = (
                "Targeting At Risk customers can focus retention efforts "
                "on customers showing weaker recent engagement while protecting "
                "existing customer value."
            )

            return _build_response(
                question,
                findings,
                actions,
                impact,
            )

    # =========================================================
    # 2. WHY ARE CUSTOMERS AT RISK?
    # =========================================================

    if (
        "why" in question_lower
        and "risk" in question_lower
    ):

        if at_risk:

            findings = [
                (
                    f"At Risk customers have an average recency of "
                    f"{at_risk['avg_recency_days']} days."
                ),
                (
                    f"Their average purchase frequency is "
                    f"{at_risk['avg_frequency']}, indicating lower engagement "
                    f"than the Loyal Customers segment."
                ),
            ]

            actions = [
                "Run targeted re-engagement campaigns.",
                "Identify customers with long periods since their last purchase and prioritize them for personalized communication.",
            ]

            impact = (
                "Improving recent engagement and purchase frequency may help "
                "move At Risk customers toward stronger retention behavior."
            )

            return _build_response(
                question,
                findings,
                actions,
                impact,
            )

    # =========================================================
    # 3. COMPARE SEGMENTS
    # =========================================================

    if (
        (
            "difference" in question_lower
            or "compare" in question_lower
        )
        and (
            "loyal" in question_lower
            or "risk" in question_lower
        )
    ):

        if at_risk and loyal:

            findings = [
                (
                    f"Loyal Customers have lower average recency "
                    f"({loyal['avg_recency_days']} days) than At Risk customers "
                    f"({at_risk['avg_recency_days']} days)."
                ),
                (
                    f"Loyal Customers have higher average frequency "
                    f"({loyal['avg_frequency']}) than At Risk customers "
                    f"({at_risk['avg_frequency']})."
                ),
                (
                    f"Average monetary value is "
                    f"{loyal['avg_monetary_value']:.2f} for Loyal Customers "
                    f"versus {at_risk['avg_monetary_value']:.2f} for At Risk customers."
                ),
            ]

            actions = [
                "Protect Loyal Customers with loyalty and repeat-purchase programs.",
                "Use re-engagement campaigns to improve At Risk customer activity.",
            ]

            impact = (
                "A differentiated strategy allows the business to protect "
                "high-engagement customers while addressing declining engagement "
                "among At Risk customers."
            )

            return _build_response(
                question,
                findings,
                actions,
                impact,
            )

    # =========================================================
    # 4. HIGHEST-VALUE CLUSTER
    # =========================================================

    if (
        "highest" in question_lower
        and "value" in question_lower
    ):

        if highest_value_cluster:

            cluster_id = highest_value_cluster["cluster_id"]

            findings = [
                (
                    f"Cluster {cluster_id} has the highest average monetary value "
                    f"at {highest_value_cluster['avg_monetary_value']:.2f}."
                ),
                (
                    f"Cluster {cluster_id} contains "
                    f"{highest_value_cluster['customer_count']} customers."
                ),
                (
                    f"Its average recency is "
                    f"{highest_value_cluster['avg_recency_days']} days and "
                    f"average frequency is "
                    f"{highest_value_cluster['avg_frequency']}."
                ),
            ]

            actions = [
                "Prioritize this cluster for high-value retention and upselling strategies.",
                "Analyze the products and offers most relevant to this customer group.",
            ]

            impact = (
                "Protecting the highest-value cluster can help preserve "
                "customers with strong monetary contribution."
            )

            return _build_response(
                question,
                findings,
                actions,
                impact,
            )

    # =========================================================
    # 5. LARGEST CUSTOMER SEGMENT
    # =========================================================

    if (
        "most customers" in question_lower
        or "largest segment" in question_lower
    ):

        if segments:

            largest_segment = max(
                segments,
                key=lambda x: x["customer_count"]
            )

            findings = [
                (
                    f"{largest_segment['segment']} is the largest customer "
                    f"segment with {largest_segment['customer_count']} customers."
                ),
                (
                    f"It represents {largest_segment['customer_percentage']}% "
                    f"of the customer base."
                ),
            ]

            actions = [
                f"Prioritize {largest_segment['segment']} when designing broad customer strategies.",
                "Use segment-specific campaigns based on engagement behavior.",
            ]

            impact = (
                "Focusing on the largest segment can provide broad coverage "
                "for customer engagement initiatives."
            )

            return _build_response(
                question,
                findings,
                actions,
                impact,
            )

    # =========================================================
    # 6. HIGHEST MONETARY VALUE SEGMENT
    # =========================================================

    if (
        "highest monetary" in question_lower
        or "highest value segment" in question_lower
        or "most valuable segment" in question_lower
    ):

        if segments:

            highest_value_segment = max(
                segments,
                key=lambda x: x["avg_monetary_value"]
            )

            findings = [
                (
                    f"{highest_value_segment['segment']} has the highest "
                    f"average monetary value at "
                    f"{highest_value_segment['avg_monetary_value']:.2f}."
                ),
                (
                    f"This segment contains "
                    f"{highest_value_segment['customer_count']} customers."
                ),
            ]

            actions = [
                f"Prioritize {highest_value_segment['segment']} for value-preservation strategies.",
                "Develop personalized offers to encourage continued engagement.",
            ]

            impact = (
                "Protecting the highest-value segment can help preserve "
                "customers with strong monetary contribution."
            )

            return _build_response(
                question,
                findings,
                actions,
                impact,
            )

    # =========================================================
    # 7. HIGHEST PURCHASE FREQUENCY SEGMENT
    # =========================================================

    if (
        "highest purchase frequency" in question_lower
        or "highest frequency" in question_lower
    ):

        if segments:

            highest_frequency_segment = max(
                segments,
                key=lambda x: x["avg_frequency"]
            )

            findings = [
                (
                    f"{highest_frequency_segment['segment']} has the highest "
                    f"average purchase frequency at "
                    f"{highest_frequency_segment['avg_frequency']}."
                ),
                (
                    f"This segment contains "
                    f"{highest_frequency_segment['customer_count']} customers."
                ),
            ]

            actions = [
                "Use repeat-purchase and loyalty strategies to maintain engagement.",
                "Analyze what drives the higher purchasing frequency.",
            ]

            impact = (
                "Maintaining high purchase frequency can support continued "
                "customer engagement and repeat business."
            )

            return _build_response(
                question,
                findings,
                actions,
                impact,
            )

    # =========================================================
    # 8. BEST RECENCY SEGMENT
    # =========================================================

    if (
        "best recency" in question_lower
        or "lowest recency" in question_lower
        or "most recent" in question_lower
    ):

        if segments:

            best_recency_segment = min(
                segments,
                key=lambda x: x["avg_recency_days"]
            )

            findings = [
                (
                    f"{best_recency_segment['segment']} has the lowest "
                    f"average recency at "
                    f"{best_recency_segment['avg_recency_days']} days."
                ),
                (
                    f"This segment contains "
                    f"{best_recency_segment['customer_count']} customers."
                ),
            ]

            actions = [
                "Use this segment as a benchmark for recent customer engagement.",
                "Analyze the behaviors associated with stronger recency.",
            ]

            impact = (
                "Understanding stronger recency behavior can help identify "
                "patterns associated with active customers."
            )

            return _build_response(
                question,
                findings,
                actions,
                impact,
            )

    # =========================================================
    # 9. LARGEST CLUSTER
    # =========================================================

    if (
        "most customers" in question_lower
        and "cluster" in question_lower
    ):

        if clusters:

            largest_cluster = max(
                clusters,
                key=lambda x: x["customer_count"]
            )

            findings = [
                (
                    f"Cluster {largest_cluster['cluster_id']} is the largest "
                    f"cluster with {largest_cluster['customer_count']} customers."
                ),
                (
                    f"Its average monetary value is "
                    f"{largest_cluster['avg_monetary_value']:.2f}."
                ),
            ]

            actions = [
                "Use this cluster as an important audience for scalable customer strategies.",
                "Analyze the behavior of this large customer group for targeted campaigns.",
            ]

            impact = (
                "Understanding the largest behavioral cluster can support "
                "scalable customer engagement strategies."
            )

            return _build_response(
                question,
                findings,
                actions,
                impact,
            )

    # =========================================================
    # 10. HIGHEST-FREQUENCY CLUSTER
    # =========================================================

    if (
        "highest purchase frequency" in question_lower
        and "cluster" in question_lower
    ):

        if clusters:

            highest_frequency_cluster = max(
                clusters,
                key=lambda x: x["avg_frequency"]
            )

            findings = [
                (
                    f"Cluster {highest_frequency_cluster['cluster_id']} has the "
                    f"highest average purchase frequency at "
                    f"{highest_frequency_cluster['avg_frequency']}."
                ),
                (
                    f"This cluster contains "
                    f"{highest_frequency_cluster['customer_count']} customers."
                ),
            ]

            actions = [
                "Protect the purchasing behavior of this highly active cluster.",
                "Analyze the factors associated with its higher purchase frequency.",
            ]

            impact = (
                "Maintaining high-frequency customer behavior can support "
                "continued repeat purchasing."
            )

            return _build_response(
                question,
                findings,
                actions,
                impact,
            )

    # =========================================================
    # 11. BEST RECENCY CLUSTER
    # =========================================================

    if (
        "best recency" in question_lower
        and "cluster" in question_lower
    ):

        if clusters:

            best_recency_cluster = min(
                clusters,
                key=lambda x: x["avg_recency_days"]
            )

            findings = [
                (
                    f"Cluster {best_recency_cluster['cluster_id']} has the "
                    f"lowest average recency at "
                    f"{best_recency_cluster['avg_recency_days']} days."
                ),
                (
                    f"This cluster contains "
                    f"{best_recency_cluster['customer_count']} customers."
                ),
            ]

            actions = [
                "Use this cluster as a benchmark for recent customer activity.",
                "Analyze the behaviors contributing to stronger recency.",
            ]

            impact = (
                "Understanding highly recent customer behavior can help "
                "identify patterns associated with active engagement."
            )

            return _build_response(
                question,
                findings,
                actions,
                impact,
            )

    # =========================================================
    # 12. UPSELLING
    # =========================================================

    if (
        "upsell" in question_lower
        or "upselling" in question_lower
    ):

        if highest_value_cluster:

            findings = [
                (
                    f"Cluster {highest_value_cluster['cluster_id']} has the "
                    f"highest average monetary value at "
                    f"{highest_value_cluster['avg_monetary_value']:.2f}."
                ),
                (
                    f"The cluster contains "
                    f"{highest_value_cluster['customer_count']} customers "
                    f"with an average frequency of "
                    f"{highest_value_cluster['avg_frequency']}."
                ),
            ]

            actions = [
                "Prioritize the highest-value cluster for upselling opportunities.",
                "Develop offers aligned with the purchasing behavior of this cluster.",
            ]

            impact = (
                "Targeting customers with stronger monetary contribution "
                "can support value-focused growth strategies."
            )

            return _build_response(
                question,
                findings,
                actions,
                impact,
            )

    # =========================================================
    # 13. RE-ENGAGEMENT
    # =========================================================

    if (
        "re-engagement" in question_lower
        or "reengagement" in question_lower
        or "re engagement" in question_lower
    ):

        if at_risk:

            findings = [
                (
                    f"At Risk customers represent "
                    f"{at_risk['customer_count']} customers "
                    f"({at_risk['customer_percentage']}%) of the customer base."
                ),
                (
                    f"Their average recency is "
                    f"{at_risk['avg_recency_days']} days."
                ),
            ]

            actions = [
                "Focus re-engagement campaigns on the At Risk segment.",
                "Use personalized reminders and offers to encourage repeat purchases.",
            ]

            impact = (
                "Re-engagement efforts can focus resources on customers "
                "showing weaker recent activity."
            )

            return _build_response(
                question,
                findings,
                actions,
                impact,
            )

    # =========================================================
    # 14. CUSTOMER BASE SUMMARY
    # =========================================================

    if (
        "summary" in question_lower
        or "summarize" in question_lower
        or "customer base" in question_lower
    ):

        findings = [
            (
                f"The customer base contains "
                f"{overall['total_customers']} customers."
            ),
            (
                f"Total monetary value is "
                f"{overall['total_monetary_value']:.2f}."
            ),
            (
                f"Average customer recency is "
                f"{overall['avg_recency_days']} days and average frequency is "
                f"{overall['avg_frequency']}."
            ),
        ]

        if at_risk and loyal:

            findings.append(
                (
                    f"The customer base is split between "
                    f"{at_risk['customer_count']} At Risk customers and "
                    f"{loyal['customer_count']} Loyal Customers."
                )
            )

        actions = [
            "Prioritize retention efforts for the At Risk segment.",
            "Continue loyalty and value-building strategies for Loyal Customers.",
        ]

        impact = (
            "Using segment-specific strategies can help balance customer "
            "retention with continued engagement of high-value customers."
        )

        return _build_response(
            question,
            findings,
            actions,
            impact,
        )

    # =========================================================
    # 15. IMPROVE CUSTOMER LOYALTY
    # =========================================================

    if (
        "improve customer loyalty" in question_lower
        or "improve loyalty" in question_lower
        or "increase customer loyalty" in question_lower
        or "increase loyalty" in question_lower
    ):

        if loyal and at_risk:

            findings = [
                (
                    f"Loyal Customers have higher average purchase frequency "
                    f"({loyal['avg_frequency']}) than At Risk customers "
                    f"({at_risk['avg_frequency']})."
                ),
                (
                    f"Loyal Customers also have lower average recency "
                    f"({loyal['avg_recency_days']} days), indicating stronger "
                    f"recent engagement."
                ),
            ]

            actions = [
                "Strengthen loyalty programs for customers already showing strong engagement.",
                "Use re-engagement campaigns to move At Risk customers toward stronger purchasing behavior.",
            ]

            impact = (
                "A combination of loyalty and re-engagement strategies can "
                "strengthen existing customer relationships while addressing weaker engagement."
            )

            return _build_response(
                question,
                findings,
                actions,
                impact,
            )


    # =========================================================
    # 16. CUSTOMERS NEEDING IMMEDIATE ATTENTION
    # =========================================================

    if (
        "immediate attention" in question_lower
        or "customers need attention" in question_lower
        or "customers need urgent attention" in question_lower
    ):

        if at_risk:

            findings = [
                (
                    f"At Risk customers represent "
                    f"{at_risk['customer_count']} customers "
                    f"({at_risk['customer_percentage']}%) of the customer base."
                ),
                (
                    f"Their average recency is "
                    f"{at_risk['avg_recency_days']} days, indicating weaker "
                    f"recent engagement."
                ),
            ]

            actions = [
                "Prioritize At Risk customers for immediate retention activity.",
                "Use personalized re-engagement communication for customers with weaker recent activity.",
            ]

            impact = (
                "Early intervention can help address weaker engagement before "
                "customers become harder to retain."
            )

            return _build_response(
                question,
                findings,
                actions,
                impact,
            )


    # =========================================================
    # 17. MOST VALUABLE CUSTOMERS
    # =========================================================

    if (
        "most valuable customers" in question_lower
        or "which customers are most valuable" in question_lower
        or "highest value customers" in question_lower
    ):

        if highest_value_cluster:

            findings = [
                (
                    f"Cluster {highest_value_cluster['cluster_id']} has the "
                    f"highest average monetary value at "
                    f"{highest_value_cluster['avg_monetary_value']:.2f}."
                ),
                (
                    f"This cluster contains "
                    f"{highest_value_cluster['customer_count']} customers."
                ),
            ]

            actions = [
                "Prioritize this cluster for high-value retention strategies.",
                "Explore upselling and personalized offers for this customer group.",
            ]

            impact = (
                "Protecting the highest-value customers can help preserve "
                "strong customer value and support targeted growth."
            )

            return _build_response(
                question,
                findings,
                actions,
                impact,
            )


    # =========================================================
    # 18. MOST ENGAGED CUSTOMERS
    # =========================================================

    if (
        "most engaged customers" in question_lower
        or "most engaged" in question_lower
        or "highest engagement" in question_lower
    ):

        if clusters:

            most_engaged_cluster = min(
                clusters,
                key=lambda x: x["avg_recency_days"]
            )

            findings = [
                (
                    f"Cluster {most_engaged_cluster['cluster_id']} has the "
                    f"lowest average recency at "
                    f"{most_engaged_cluster['avg_recency_days']} days."
                ),
                (
                    f"Its average purchase frequency is "
                    f"{most_engaged_cluster['avg_frequency']}."
                ),
            ]

            actions = [
                "Use this cluster as a benchmark for strong customer engagement.",
                "Analyze the behaviors and offers associated with its recent activity.",
            ]

            impact = (
                "Understanding highly engaged customers can help identify "
                "behaviors that support stronger ongoing customer activity."
            )

            return _build_response(
                question,
                findings,
                actions,
                impact,
            )


    # =========================================================
    # 19. CHURN RISK
    # =========================================================

    if (
        "signs of churn" in question_lower
        or "churn risk" in question_lower
        or "likely to churn" in question_lower
        or "at risk of churn" in question_lower
    ):

        if at_risk:

            findings = [
                (
                    f"At Risk customers have an average recency of "
                    f"{at_risk['avg_recency_days']} days."
                ),
                (
                    f"Their average purchase frequency is "
                    f"{at_risk['avg_frequency']}, indicating weaker "
                    f"engagement than Loyal Customers."
                ),
            ]

            actions = [
                "Prioritize At Risk customers for churn-prevention campaigns.",
                "Use personalized re-engagement strategies to encourage repeat purchases.",
            ]

            impact = (
                "Focusing on customers showing weaker recent engagement can "
                "support early churn-prevention efforts."
            )

            return _build_response(
                question,
                findings,
                actions,
                impact,
            )

    # =========================================================
    # DYNAMIC GENAI FALLBACK
    # =========================================================

    return _generate_dynamic_insight(question)
