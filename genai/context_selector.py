def select_relevant_context(question, metrics):
    """
    Select only the verified business metrics relevant to the question.
    """

    question_lower = question.lower().strip()

    overall = metrics["overall"]
    segments = metrics["segments"]
    clusters = metrics["clusters"]
    highest_value_cluster = metrics["highest_value_cluster"]

    context = {}

    # ---------------------------------------------------------
    # Retention / engagement questions
    # ---------------------------------------------------------

    if any(
        keyword in question_lower
        for keyword in [
            "retention",
            "engagement",
            "at risk",
            "churn",
            "re-engagement",
            "repeat purchase",
        ]
    ):

        context["segments"] = segments

        return context

    # ---------------------------------------------------------
    # Cluster questions
    # ---------------------------------------------------------

    if "cluster" in question_lower:

        context["clusters"] = clusters

        if highest_value_cluster:
            context["highest_value_cluster"] = highest_value_cluster

        return context

    # ---------------------------------------------------------
    # Customer value / monetary questions
    # ---------------------------------------------------------

    if any(
        keyword in question_lower
        for keyword in [
            "customer value",
            "monetary",
            "valuable",
            "high value",
            "upsell",
            "upselling",
        ]
    ):

        context["segments"] = segments
        context["clusters"] = clusters

        if highest_value_cluster:
            context["highest_value_cluster"] = highest_value_cluster

        return context

    # ---------------------------------------------------------
    # General summary questions
    # ---------------------------------------------------------

    if any(
        keyword in question_lower
        for keyword in [
            "summary",
            "summarize",
            "overview",
            "overall picture",
        ]
    ):

        context["overall"] = overall
        context["segments"] = segments

        return context

    # ---------------------------------------------------------
    # Unknown / general business question
    # ---------------------------------------------------------

    context["overall"] = overall
    context["segments"] = segments
    context["clusters"] = clusters

    return context
