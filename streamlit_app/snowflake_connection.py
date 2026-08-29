import snowflake.connector


def get_snowflake_connection():
    """
    Create and return a Snowflake connection
    using environment variables.
    """

    return snowflake.connector.connect(
        user="JAYANT2026",
        password="#EasyLife&50LPA",
        account="CTSPNQO-AF84102",
        warehouse="AI_CUSTOMER_WH",
        database="AI_CUSTOMER_DB",
        schema="ANALYTICS",
        role="ACCOUNTADMIN",
    )
