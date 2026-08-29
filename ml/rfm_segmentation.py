"""
AI Customer Intelligence Platform
---------------------------------
RFM-based customer segmentation using K-Means.

This module contains ONLY ML logic.
Snowflake/Airflow connectivity is handled by the Airflow DAG.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

RFM_FEATURES = [
    "RECENCY_DAYS",
    "FREQUENCY",
    "MONETARY_VALUE",
]

# Evaluate multiple K values for model comparison.
K_RANGE = range(2, 7)

# Business-oriented final model.
# We intentionally do not automatically select the
# highest silhouette K because K=2 is too coarse
# for customer intelligence.
FINAL_K = 4

RANDOM_STATE = 42
N_INIT = 10


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate_rfm_data(df: pd.DataFrame) -> None:
    """Validate the input RFM dataset."""

    required_columns = [
        "CUSTOMER_ID",
        "RECENCY_DAYS",
        "FREQUENCY",
        "MONETARY_VALUE",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if df.empty:
        raise ValueError("RFM dataset is empty.")

    if df["CUSTOMER_ID"].duplicated().any():
        raise ValueError(
            "Duplicate CUSTOMER_ID values found."
        )

    if df[RFM_FEATURES].isnull().any().any():
        raise ValueError(
            "NULL values found in RFM features."
        )

    if (df["RECENCY_DAYS"] < 0).any():
        raise ValueError(
            "RECENCY_DAYS contains negative values."
        )

    if (df["FREQUENCY"] <= 0).any():
        raise ValueError(
            "FREQUENCY contains zero/negative values."
        )

    if (df["MONETARY_VALUE"] <= 0).any():
        raise ValueError(
            "MONETARY_VALUE contains zero/negative values."
        )

    print("\nRFM validation: SUCCESS")
    print(f"Customers: {len(df):,}")


# ---------------------------------------------------------
# RFM SCORING
# ---------------------------------------------------------

def calculate_rfm_scores(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate traditional 1-5 RFM scores.

    Recency:
        Lower number of days is better.

    Frequency:
        Higher frequency is better.

    Monetary:
        Higher monetary value is better.
    """

    result = df.copy()

    # qcut can occasionally produce duplicate bin edges.
    # rank(method='first') guarantees unique ordering.
    result["RECENCY_SCORE"] = pd.qcut(
        result["RECENCY_DAYS"].rank(method="first"),
        q=5,
        labels=[5, 4, 3, 2, 1],
    ).astype(int)

    result["FREQUENCY_SCORE"] = pd.qcut(
        result["FREQUENCY"].rank(method="first"),
        q=5,
        labels=[1, 2, 3, 4, 5],
    ).astype(int)

    result["MONETARY_SCORE"] = pd.qcut(
        result["MONETARY_VALUE"].rank(method="first"),
        q=5,
        labels=[1, 2, 3, 4, 5],
    ).astype(int)

    result["RFM_SCORE"] = (
        result["RECENCY_SCORE"].astype(str)
        + result["FREQUENCY_SCORE"].astype(str)
        + result["MONETARY_SCORE"].astype(str)
    )

    result["RFM_TOTAL_SCORE"] = (
        result["RECENCY_SCORE"]
        + result["FREQUENCY_SCORE"]
        + result["MONETARY_SCORE"]
    )

    print("\nRFM scoring: SUCCESS")
    print("Scores generated: 1-5")
    print("RFM score format: Recency-Frequency-Monetary")

    return result


# ---------------------------------------------------------
# PREPROCESSING
# ---------------------------------------------------------

def prepare_rfm_features(df: pd.DataFrame):
    """
    Apply log transformation and standard scaling.

    Log transformation reduces skewness, especially
    for monetary values.
    """

    features = df[RFM_FEATURES].copy()

    features["RECENCY_DAYS"] = np.log1p(
        features["RECENCY_DAYS"]
    )

    features["FREQUENCY"] = np.log1p(
        features["FREQUENCY"]
    )

    features["MONETARY_VALUE"] = np.log1p(
        features["MONETARY_VALUE"]
    )

    scaler = StandardScaler()

    scaled_features = scaler.fit_transform(features)

    scaled_df = pd.DataFrame(
        scaled_features,
        columns=RFM_FEATURES,
        index=df.index,
    )

    print("\nRFM preprocessing: SUCCESS")
    print("Applied:")
    print("  - log1p transformation")
    print("  - StandardScaler")

    return scaled_df, scaler


# ---------------------------------------------------------
# FIND BEST K
# ---------------------------------------------------------

def evaluate_k_values(
    scaled_features: pd.DataFrame,
) -> pd.DataFrame:
    """
    Evaluate K-Means for K=2 through K=6.
    """

    results = []

    print("\n" + "=" * 60)
    print("K-MEANS MODEL EVALUATION")
    print("=" * 60)

    for k in K_RANGE:

        model = KMeans(
            n_clusters=k,
            random_state=RANDOM_STATE,
            n_init=N_INIT,
        )

        labels = model.fit_predict(
            scaled_features
        )

        silhouette = silhouette_score(
            scaled_features,
            labels,
        )

        inertia = model.inertia_

        results.append(
            {
                "K": k,
                "SILHOUETTE_SCORE": round(
                    silhouette,
                    4,
                ),
                "INERTIA": round(
                    inertia,
                    2,
                ),
            }
        )

        print(
            f"K={k} | "
            f"Silhouette={silhouette:.4f} | "
            f"Inertia={inertia:.2f}"
        )

    results_df = pd.DataFrame(results)

    statistical_best_k = int(
        results_df.loc[
            results_df["SILHOUETTE_SCORE"].idxmax(),
            "K",
        ]
    )

    results_df["STATISTICAL_BEST_K"] = (
        statistical_best_k
    )

    results_df["BUSINESS_SELECTED_K"] = FINAL_K

    print(
        "\nBest K based on silhouette:",
        statistical_best_k,
    )

    print(
        "Business-selected final K:",
        FINAL_K,
    )

    return results_df


# ---------------------------------------------------------
# TRAIN FINAL MODEL
# ---------------------------------------------------------

def train_kmeans(
    scaled_features: pd.DataFrame,
    final_k: int,
):
    """Train the final K-Means model."""

    model = KMeans(
        n_clusters=final_k,
        random_state=RANDOM_STATE,
        n_init=N_INIT,
    )

    labels = model.fit_predict(
        scaled_features
    )

    print("\nFinal K-Means model trained successfully.")
    print(f"Final clusters: {final_k}")

    return model, labels


# ---------------------------------------------------------
# CLUSTER PROFILING
# ---------------------------------------------------------

def profile_clusters(
    df: pd.DataFrame,
    labels,
) -> pd.DataFrame:
    """
    Create cluster statistics using original RFM values.
    """

    profile_df = df.copy()

    profile_df["CLUSTER_ID"] = labels

    profile = (
        profile_df
        .groupby("CLUSTER_ID")
        .agg(
            CUSTOMER_COUNT=("CUSTOMER_ID", "count"),
            AVG_RECENCY_DAYS=("RECENCY_DAYS", "mean"),
            AVG_FREQUENCY=("FREQUENCY", "mean"),
            AVG_MONETARY_VALUE=("MONETARY_VALUE", "mean"),
            MEDIAN_RECENCY_DAYS=("RECENCY_DAYS", "median"),
            MEDIAN_FREQUENCY=("FREQUENCY", "median"),
            MEDIAN_MONETARY_VALUE=("MONETARY_VALUE", "median"),
        )
        .reset_index()
    )

    return profile


# ---------------------------------------------------------
# BUSINESS LABELS
# ---------------------------------------------------------

def assign_business_labels(
    profile: pd.DataFrame,
) -> pd.DataFrame:
    """
    Assign business-friendly labels based on actual
    cluster characteristics.

    Labels are NOT based on cluster IDs.
    """

    profile = profile.copy()

    # Calculate normalized ranks.
    # Higher rank means stronger customer behavior.

    profile["RECENCY_RANK"] = profile[
        "AVG_RECENCY_DAYS"
    ].rank(
        ascending=True,
        method="min",
    )

    profile["FREQUENCY_RANK"] = profile[
        "AVG_FREQUENCY"
    ].rank(
        ascending=False,
        method="min",
    )

    profile["MONETARY_RANK"] = profile[
        "AVG_MONETARY_VALUE"
    ].rank(
        ascending=False,
        method="min",
    )

    cluster_count = len(profile)

    labels = []

    for _, row in profile.iterrows():

        recency_rank = row["RECENCY_RANK"]
        frequency_rank = row["FREQUENCY_RANK"]
        monetary_rank = row["MONETARY_RANK"]

        # Best overall customer group.
        if (
            recency_rank == 1
            and frequency_rank == 1
            and monetary_rank == 1
        ):
            label = "Champions"

        # Strong frequency/value but not necessarily
        # the most recent.
        elif (
            frequency_rank <= 2
            and monetary_rank <= 2
        ):
            label = "Loyal Customers"

        # Valuable customers whose recency is weaker.
        elif (
            monetary_rank <= 2
            and recency_rank > 2
        ):
            label = "At Risk High Value"

        # Recent customers with developing engagement.
        elif recency_rank <= 2:
            label = "Potential Loyalists"

        else:
            label = "At Risk"

        labels.append(label)

    profile["SEGMENT_NAME"] = labels

    profile = profile.drop(
        columns=[
            "RECENCY_RANK",
            "FREQUENCY_RANK",
            "MONETARY_RANK",
        ]
    )

    return profile


# ---------------------------------------------------------
# BUILD CUSTOMER SEGMENT DATASET
# ---------------------------------------------------------

def build_customer_segments(
    df: pd.DataFrame,
    labels,
    cluster_profile: pd.DataFrame,
) -> pd.DataFrame:
    """Create customer-level segmentation output."""

    result = df.copy()

    result["CLUSTER_ID"] = labels

    label_mapping = cluster_profile[
        [
            "CLUSTER_ID",
            "SEGMENT_NAME",
        ]
    ]

    result = result.merge(
        label_mapping,
        on="CLUSTER_ID",
        how="left",
    )

    return result


# ---------------------------------------------------------
# OUTPUT VALIDATION
# ---------------------------------------------------------

def validate_segmentation_output(
    customer_segments: pd.DataFrame,
    cluster_profile: pd.DataFrame,
) -> None:
    """Validate the final segmentation result."""

    if customer_segments.empty:
        raise ValueError(
            "Customer segmentation output is empty."
        )

    required_columns = [
        "CUSTOMER_ID",
        "CLUSTER_ID",
        "SEGMENT_NAME",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in customer_segments.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required segmentation columns: "
            f"{missing_columns}"
        )

    if customer_segments["CUSTOMER_ID"].duplicated().any():
        raise ValueError(
            "Duplicate customers found in segmentation output."
        )

    if customer_segments["CLUSTER_ID"].isnull().any():
        raise ValueError(
            "Customers without a cluster were found."
        )

    if customer_segments["SEGMENT_NAME"].isnull().any():
        raise ValueError(
            "Customers without a segment name were found."
        )

    total_cluster_customers = int(
        cluster_profile["CUSTOMER_COUNT"].sum()
    )

    if total_cluster_customers != len(customer_segments):
        raise ValueError(
            "Cluster profile customer count does not match "
            "customer segmentation row count."
        )

    unique_clusters = customer_segments["CLUSTER_ID"].nunique()

    profile_clusters = cluster_profile["CLUSTER_ID"].nunique()

    if unique_clusters != profile_clusters:
        raise ValueError(
            "Customer segmentation cluster count does not "
            "match cluster profile cluster count."
        )

    if cluster_profile["SEGMENT_NAME"].isnull().any():
        raise ValueError(
            "Cluster profile contains NULL segment names."
        )

    print("\nSegmentation validation: SUCCESS")
    print(
        f"Customers segmented: "
        f"{len(customer_segments):,}"
    )
    print(
        f"Unique customers: "
        f"{customer_segments['CUSTOMER_ID'].nunique():,}"
    )
    print(
        f"Clusters generated: "
        f"{unique_clusters}"
    )

# ---------------------------------------------------------
# SAVE RESULTS
# ---------------------------------------------------------

def save_results(
    customer_segments: pd.DataFrame,
    cluster_profile: pd.DataFrame,
    model_evaluation: pd.DataFrame,
) -> None:
    """Save ML outputs locally for validation."""

    output_dir = Path("ml/output")

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    customer_segments.to_csv(
        output_dir / "customer_segments.csv",
        index=False,
    )

    cluster_profile.to_csv(
        output_dir / "cluster_profile.csv",
        index=False,
    )

    model_evaluation.to_csv(
        output_dir / "model_evaluation.csv",
        index=False,
    )

    print("\nML output files created:")

    print(
        f"  {output_dir / 'customer_segments.csv'}"
    )

    print(
        f"  {output_dir / 'cluster_profile.csv'}"
    )

    print(
        f"  {output_dir / 'model_evaluation.csv'}"
    )


# ---------------------------------------------------------
# MAIN ML PIPELINE
# ---------------------------------------------------------

def run_segmentation(df: pd.DataFrame):
    """
    Complete RFM segmentation pipeline.

    Returns:
        customer_segments
        cluster_profile
        model_evaluation
        model
        scaler
    """

    print("\n" + "=" * 60)
    print("AI CUSTOMER INTELLIGENCE")
    print("RFM CUSTOMER SEGMENTATION")
    print("=" * 60)

    # -----------------------------------------------------
    # 1. Validate input
    # -----------------------------------------------------

    validate_rfm_data(df)

    # -----------------------------------------------------
    # 2. Calculate traditional RFM scores
    # -----------------------------------------------------

    scored_df = calculate_rfm_scores(df)

    # -----------------------------------------------------
    # 3. Prepare ML features
    # -----------------------------------------------------

    scaled_features, scaler = prepare_rfm_features(
        scored_df
    )

    # -----------------------------------------------------
    # 4. Evaluate K=2 through K=6
    # -----------------------------------------------------

    model_evaluation = evaluate_k_values(
        scaled_features
    )

    # -----------------------------------------------------
    # 5. Train business-selected final model
    # -----------------------------------------------------

    model, labels = train_kmeans(
        scaled_features,
        FINAL_K,
    )

    # -----------------------------------------------------
    # 6. Profile clusters
    # -----------------------------------------------------

    cluster_profile = profile_clusters(
        scored_df,
        labels,
    )

    # -----------------------------------------------------
    # 7. Assign business labels
    # -----------------------------------------------------

    cluster_profile = assign_business_labels(
        cluster_profile
    )

    # -----------------------------------------------------
    # 8. Build customer-level output
    # -----------------------------------------------------

    customer_segments = build_customer_segments(
        scored_df,
        labels,
        cluster_profile,
    )

    # -----------------------------------------------------
    # 9. Validate final output
    # -----------------------------------------------------

    validate_segmentation_output(
        customer_segments,
        cluster_profile,
    )

    # -----------------------------------------------------
    # 10. Save outputs
    # -----------------------------------------------------

    save_results(
        customer_segments,
        cluster_profile,
        model_evaluation,
    )

    # -----------------------------------------------------
    # 11. Display summary
    # -----------------------------------------------------

    print("\n" + "=" * 60)
    print("SEGMENTATION COMPLETE")
    print("=" * 60)

    print("\nCluster profile:")

    print(
        cluster_profile.to_string(
            index=False
        )
    )

    print("\nSegment distribution:")

    print(
        customer_segments[
            "SEGMENT_NAME"
        ].value_counts()
    )

    return (
        customer_segments,
        cluster_profile,
        model_evaluation,
        model,
        scaler,
    )


if __name__ == "__main__":
    print(
        "This module is designed to be executed "
        "through an Airflow task."
    )
