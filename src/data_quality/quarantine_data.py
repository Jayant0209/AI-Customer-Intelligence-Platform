import pandas as pd
import os


# ---------------------------------------
# Create output directories
# ---------------------------------------

os.makedirs(
    "data/valid",
    exist_ok=True
)

os.makedirs(
    "data/quarantine",
    exist_ok=True
)


# ---------------------------------------
# Load corrupted data
# ---------------------------------------

customers = pd.read_csv(
    "data/corrupted/customers_corrupted.csv"
)

orders = pd.read_csv(
    "data/corrupted/orders_corrupted.csv"
)


# =======================================
# CUSTOMER VALIDATION
# =======================================

# ---------------------------------------
# Create validation flags
# ---------------------------------------

customers["dq_reason"] = ""


# Missing customer ID

customers.loc[
    customers["customer_id"].isna(),
    "dq_reason"
] = "MISSING_CUSTOMER_ID"


# Missing email

customers.loc[
    customers["email"].isna(),
    "dq_reason"
] = "MISSING_EMAIL"


# Invalid email

email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

invalid_email_mask = (
    ~customers["email"]
    .fillna("")
    .str.match(email_pattern)
    & customers["email"].notna()
)

customers.loc[
    invalid_email_mask,
    "dq_reason"
] = "INVALID_EMAIL"


# Invalid gender

invalid_gender_mask = ~customers[
    "gender"
].isin(
    ["Male", "Female"]
)

customers.loc[
    invalid_gender_mask,
    "dq_reason"
] = "INVALID_GENDER"


# Duplicate customer ID

duplicate_customer_mask = customers[
    "customer_id"
].duplicated(
    keep=False
)

customers.loc[
    duplicate_customer_mask,
    "dq_reason"
] = "DUPLICATE_CUSTOMER_ID"


# ---------------------------------------
# Split valid and invalid customers
# ---------------------------------------

invalid_customers = customers[
    customers["dq_reason"] != ""
].copy()

valid_customers = customers[
    customers["dq_reason"] == ""
].copy()


# =======================================
# ORDER VALIDATION
# =======================================

orders["dq_reason"] = ""


# Missing order ID

orders.loc[
    orders["order_id"].isna(),
    "dq_reason"
] = "MISSING_ORDER_ID"


# Invalid customer ID

invalid_customer_mask = ~orders[
    "customer_id"
].isin(
    customers["customer_id"]
)

orders.loc[
    invalid_customer_mask,
    "dq_reason"
] = "INVALID_CUSTOMER_ID"


# Invalid quantity

orders.loc[
    orders["quantity"] <= 0,
    "dq_reason"
] = "INVALID_QUANTITY"


# Invalid amount

orders.loc[
    orders["total_amount"] < 0,
    "dq_reason"
] = "INVALID_AMOUNT"


# Duplicate order ID

duplicate_order_mask = orders[
    "order_id"
].duplicated(
    keep=False
)

orders.loc[
    duplicate_order_mask,
    "dq_reason"
] = "DUPLICATE_ORDER_ID"


# ---------------------------------------
# Split valid and invalid orders
# ---------------------------------------

invalid_orders = orders[
    orders["dq_reason"] != ""
].copy()

valid_orders = orders[
    orders["dq_reason"] == ""
].copy()


# =======================================
# SAVE RESULTS
# =======================================

# Valid customers

valid_customers.to_csv(
    "data/valid/customers_valid.csv",
    index=False
)


# Invalid customers

invalid_customers.to_csv(
    "data/quarantine/customers_invalid.csv",
    index=False
)


# Valid orders

valid_orders.to_csv(
    "data/valid/orders_valid.csv",
    index=False
)


# Invalid orders

invalid_orders.to_csv(
    "data/quarantine/orders_invalid.csv",
    index=False
)


# =======================================
# REPORT
# =======================================

print("\n==========================================")
print("        QUARANTINE DATA REPORT")
print("==========================================")

print("\nCUSTOMERS")
print("------------------------------------------")

print(
    "Original records:",
    len(customers)
)

print(
    "Valid records:",
    len(valid_customers)
)

print(
    "Quarantined records:",
    len(invalid_customers)
)


print("\nORDERS")
print("------------------------------------------")

print(
    "Original records:",
    len(orders)
)

print(
    "Valid records:",
    len(valid_orders)
)

print(
    "Quarantined records:",
    len(invalid_orders)
)


print("\n==========================================")
print("Files created successfully!")
print("==========================================")