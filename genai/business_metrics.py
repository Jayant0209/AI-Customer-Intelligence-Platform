from streamlit_app.snowflake_connection import get_snowflake_connection


DATABASE = "AI_CUSTOMER_DB"
SCHEMA = "ANALYTICS"
TABLE = "CUSTOMER_SEGMENTS"


def get_business_metrics():
    conn = get_snowflake_connection()

    try:
        cursor = conn.cursor()

        # ---------------------------------------------------------
        # Overall customer metrics
        # ---------------------------------------------------------
        overall_query = f"""
            SELECT
                COUNT(*) AS TOTAL_CUSTOMERS,
                COALESCE(SUM(MONETARY_VALUE), 0) AS TOTAL_MONETARY_VALUE,
                COALESCE(AVG(RECENCY_DAYS), 0) AS AVG_RECENCY_DAYS,
                COALESCE(AVG(FREQUENCY), 0) AS AVG_FREQUENCY
            FROM {DATABASE}.{SCHEMA}.{TABLE}
        """

        cursor.execute(overall_query)
        overall = cursor.fetchone()

        total_customers = int(overall[0] or 0)
        total_monetary_value = float(overall[1] or 0)
        avg_recency_days = float(overall[2] or 0)
        avg_frequency = float(overall[3] or 0)

        # ---------------------------------------------------------
        # Segment metrics
        # ---------------------------------------------------------
        segment_query = f"""
            SELECT
                SEGMENT_NAME,
                COUNT(*) AS CUSTOMER_COUNT,
                ROUND(
                    COUNT(*) * 100.0 / NULLIF({total_customers}, 0),
                    2
                ) AS CUSTOMER_PERCENTAGE,
                ROUND(AVG(RECENCY_DAYS), 2) AS AVG_RECENCY_DAYS,
                ROUND(AVG(FREQUENCY), 2) AS AVG_FREQUENCY,
                ROUND(AVG(MONETARY_VALUE), 2) AS AVG_MONETARY_VALUE
            FROM {DATABASE}.{SCHEMA}.{TABLE}
            GROUP BY SEGMENT_NAME
            ORDER BY CUSTOMER_COUNT DESC
        """

        cursor.execute(segment_query)
        segment_rows = cursor.fetchall()

        segments = []

        for row in segment_rows:
            segments.append(
                {
                    "segment": row[0],
                    "customer_count": int(row[1]),
                    "customer_percentage": float(row[2] or 0),
                    "avg_recency_days": float(row[3] or 0),
                    "avg_frequency": float(row[4] or 0),
                    "avg_monetary_value": float(row[5] or 0),
                }
            )

        # ---------------------------------------------------------
        # Cluster metrics
        # ---------------------------------------------------------
        cluster_query = f"""
            SELECT
                CLUSTER_ID,
                COUNT(*) AS CUSTOMER_COUNT,
                ROUND(AVG(RECENCY_DAYS), 2) AS AVG_RECENCY_DAYS,
                ROUND(AVG(FREQUENCY), 2) AS AVG_FREQUENCY,
                ROUND(AVG(MONETARY_VALUE), 2) AS AVG_MONETARY_VALUE
            FROM {DATABASE}.{SCHEMA}.{TABLE}
            GROUP BY CLUSTER_ID
            ORDER BY CLUSTER_ID
        """

        cursor.execute(cluster_query)
        cluster_rows = cursor.fetchall()

        clusters = []

        for row in cluster_rows:
            clusters.append(
                {
                    "cluster_id": int(row[0]),
                    "customer_count": int(row[1]),
                    "avg_recency_days": float(row[2] or 0),
                    "avg_frequency": float(row[3] or 0),
                    "avg_monetary_value": float(row[4] or 0),
                }
            )

        # ---------------------------------------------------------
        # Highest-value cluster
        # ---------------------------------------------------------
        highest_value_cluster = None

        if clusters:
            highest_value_cluster = max(
                clusters,
                key=lambda x: x["avg_monetary_value"]
            )

        # ---------------------------------------------------------
        # Return structured metrics
        # ---------------------------------------------------------
        return {
            "overall": {
                "total_customers": total_customers,
                "total_monetary_value": round(total_monetary_value, 2),
                "avg_recency_days": round(avg_recency_days, 2),
                "avg_frequency": round(avg_frequency, 2),
            },
            "segments": segments,
            "clusters": clusters,
            "highest_value_cluster": highest_value_cluster,
        }

    finally:
        try:
            cursor.close()
        except Exception:
            pass

        conn.close()
