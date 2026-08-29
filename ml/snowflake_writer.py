"""
Snowflake persistence layer for ML customer segmentation.

Reads the locally generated customer segmentation CSV
and writes it to Snowflake ANALYTICS.CUSTOMER_SEGMENTS.
"""

from pathlib import Path

import pandas as pd
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook


SNOWFLAKE_CONN_ID = "snowflake_default"

DATABASE = "AI_CUSTOMER_DB"
SCHEMA = "ANALYTICS"
TABLE = "CUSTOMER_SEGMENTS"

CSV_PATH = Path(
    "/home/asus/ai_customer_airflow/ml/output/customer_segments.csv"
)


def load_customer_segments_csv() -> pd.DataFrame:
    """Load and validate the ML segmentation CSV."""

    print("=" * 60)
    print("LOADING CUSTOMER SEGMENTATION OUTPUT")
    print("=" * 60)

    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Segmentation file not found: {CSV_PATH}"
        )

    df = pd.read_csv(CSV_PATH)

    print(f"Rows loaded: {len(df):,}")
    print(f"Columns loaded: {len(df.columns)}")

    if df.empty:
        raise ValueError(
            "Customer segmentation CSV is empty."
        )

    required_columns = [
        "CUSTOMER_ID",
        "FIRST_NAME",
        "LAST_NAME",
        "EMAIL",
        "CITY",
        "STATE",
        "CUSTOMER_SEGMENT",
        "RECENCY_DAYS",
        "FREQUENCY",
        "MONETARY_VALUE",
        "FIRST_ORDER_DATE",
        "LAST_ORDER_DATE",
        "RECENCY_SCORE",
        "FREQUENCY_SCORE",
        "MONETARY_SCORE",
        "RFM_SCORE",
        "RFM_TOTAL_SCORE",
        "CLUSTER_ID",
        "SEGMENT_NAME",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    if df["CUSTOMER_ID"].duplicated().any():
        raise ValueError(
            "Duplicate CUSTOMER_ID values found."
        )

    if df["CUSTOMER_ID"].isnull().any():
        raise ValueError(
            "NULL CUSTOMER_ID values found."
        )

    if df["CLUSTER_ID"].isnull().any():
        raise ValueError(
            "NULL CLUSTER_ID values found."
        )

    if df["SEGMENT_NAME"].isnull().any():
        raise ValueError(
            "NULL SEGMENT_NAME values found."
        )

    print("CSV validation: SUCCESS")

    return df


def write_customer_segments() -> int:
    """
    Replace the existing CUSTOMER_SEGMENTS table
    with the latest ML segmentation output.
    """

    df = load_customer_segments_csv()

    print("\nConnecting to Snowflake...")

    hook = SnowflakeHook(
        snowflake_conn_id=SNOWFLAKE_CONN_ID
    )

    conn = hook.get_conn()
    cursor = conn.cursor()

    try:
        print("Snowflake connection: SUCCESS")

        cursor.execute(
            f"""
            TRUNCATE TABLE
            {DATABASE}.{SCHEMA}.{TABLE}
            """
        )

        print("Existing CUSTOMER_SEGMENTS data cleared.")

        insert_sql = f"""
            INSERT INTO {DATABASE}.{SCHEMA}.{TABLE}
            (
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
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
        """

        records = [
            tuple(row)
            for row in df[
                [
                    "CUSTOMER_ID",
                    "FIRST_NAME",
                    "LAST_NAME",
                    "EMAIL",
                    "CITY",
                    "STATE",
                    "CUSTOMER_SEGMENT",
                    "RECENCY_DAYS",
                    "FREQUENCY",
                    "MONETARY_VALUE",
                    "FIRST_ORDER_DATE",
                    "LAST_ORDER_DATE",
                    "RECENCY_SCORE",
                    "FREQUENCY_SCORE",
                    "MONETARY_SCORE",
                    "RFM_SCORE",
                    "RFM_TOTAL_SCORE",
                    "CLUSTER_ID",
                    "SEGMENT_NAME",
                ]
            ].itertuples(index=False, name=None)
        ]

        cursor.executemany(
            insert_sql,
            records,
        )

        conn.commit()

        print(
            f"Rows written to Snowflake: {len(records):,}"
        )

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()

    return len(df)


def verify_customer_segments() -> None:
    """Verify the Snowflake ML segmentation table."""

    print("\n" + "=" * 60)
    print("VERIFYING CUSTOMER SEGMENTS IN SNOWFLAKE")
    print("=" * 60)

    hook = SnowflakeHook(
        snowflake_conn_id=SNOWFLAKE_CONN_ID
    )

    result = hook.get_first(
        f"""
        SELECT COUNT(*)
        FROM {DATABASE}.{SCHEMA}.{TABLE}
        """
    )

    row_count = int(result[0])

    print(
        f"Snowflake CUSTOMER_SEGMENTS rows: "
        f"{row_count:,}"
    )

    if row_count != 10_000:
        raise ValueError(
            f"Expected 10,000 customers but found "
            f"{row_count:,}"
        )

    print("Snowflake verification: SUCCESS")

    segment_rows = hook.get_records(
        f"""
        SELECT
            SEGMENT_NAME,
            COUNT(*) AS CUSTOMER_COUNT
        FROM {DATABASE}.{SCHEMA}.{TABLE}
        GROUP BY SEGMENT_NAME
        ORDER BY CUSTOMER_COUNT DESC
        """
    )

    print("\nSegment distribution:")

    for segment_name, customer_count in segment_rows:
        print(
            f"  {segment_name}: "
            f"{customer_count:,}"
        )


if __name__ == "__main__":
    write_customer_segments()
    verify_customer_segments()
