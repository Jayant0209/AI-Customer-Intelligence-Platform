import pandas as pd
import re


# ---------------------------------------
# Load corrupted data
# ---------------------------------------

customers = pd.read_csv(
    "data/corrupted/customers_corrupted.csv"
)

orders = pd.read_csv(
    "data/corrupted/orders_corrupted.csv"
)


# ---------------------------------------
# CUSTOMER DATA QUALITY CHECKS
# ---------------------------------------

# 1. Duplicate customers

duplicate_customers = customers[
    customers["customer_id"].duplicated(
        keep=False
    )
]


# 2. Missing customer IDs

missing_customer_ids = customers[
    customers["customer_id"].isna()
]


# 3. Missing emails

missing_emails = customers[
    customers["email"].isna()
]


# 4. Invalid emails

email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

invalid_emails = customers[
    ~customers["email"]
    .fillna("")
    .str.match(email_pattern)
]


# 5. Invalid gender

invalid_gender = customers[
    ~customers["gender"].isin(
        ["Male", "Female"]
    )
]


# ---------------------------------------
# ORDER DATA QUALITY CHECKS
# ---------------------------------------

# 6. Duplicate orders

duplicate_orders = orders[
    orders["order_id"].duplicated(
        keep=False
    )
]


# 7. Missing order IDs

missing_order_ids = orders[
    orders["order_id"].isna()
]


# 8. Invalid customer IDs

invalid_order_customers = orders[
    ~orders["customer_id"].isin(
        customers["customer_id"]
    )
]


# 9. Invalid quantities

invalid_quantities = orders[
    orders["quantity"] <= 0
]


# 10. Invalid total amounts

invalid_amounts = orders[
    orders["total_amount"] < 0
]


# ---------------------------------------
# DATA QUALITY REPORT
# ---------------------------------------

print("\n==========================================")
print("         DATA QUALITY REPORT")
print("==========================================")

print("\nCUSTOMER DATA")
print("------------------------------------------")

print(
    "Total customer records:",
    len(customers)
)

print(
    "Duplicate customer records:",
    len(duplicate_customers)
)

print(
    "Missing customer IDs:",
    len(missing_customer_ids)
)

print(
    "Missing emails:",
    len(missing_emails)
)

print(
    "Invalid emails:",
    len(invalid_emails)
)

print(
    "Invalid genders:",
    len(invalid_gender)
)


print("\nORDER DATA")
print("------------------------------------------")

print(
    "Total order records:",
    len(orders)
)

print(
    "Duplicate order records:",
    len(duplicate_orders)
)

print(
    "Missing order IDs:",
    len(missing_order_ids)
)

print(
    "Invalid customer IDs:",
    len(invalid_order_customers)
)

print(
    "Invalid quantities:",
    len(invalid_quantities)
)

print(
    "Invalid amounts:",
    len(invalid_amounts)
)


# ---------------------------------------
# Overall status
# ---------------------------------------

total_issues = (
    len(duplicate_customers)
    + len(missing_customer_ids)
    + len(missing_emails)
    + len(invalid_emails)
    + len(invalid_gender)
    + len(duplicate_orders)
    + len(missing_order_ids)
    + len(invalid_order_customers)
    + len(invalid_quantities)
    + len(invalid_amounts)
)


print("\n==========================================")

if total_issues == 0:

    print("DATA QUALITY STATUS: PASSED")

else:

    print("DATA QUALITY STATUS: FAILED")

print(
    "Total detected issues:",
    total_issues
)

print("==========================================")