import pandas as pd
import numpy as np


SEED = 42

np.random.seed(SEED)


# ---------------------------------------
# Load clean data
# ---------------------------------------

customers = pd.read_csv(
    "data/raw/customers.csv"
)

orders = pd.read_csv(
    "data/raw/orders.csv"
)


# ---------------------------------------
# CUSTOMER DATA ISSUES
# ---------------------------------------

# Missing emails

missing_email_indices = np.random.choice(
    customers.index,
    size=50,
    replace=False
)

customers.loc[
    missing_email_indices,
    "email"
] = np.nan


# Invalid emails

invalid_email_indices = np.random.choice(
    customers.index,
    size=50,
    replace=False
)

customers.loc[
    invalid_email_indices,
    "email"
] = "invalid-email"


# Invalid gender

invalid_gender_indices = np.random.choice(
    customers.index,
    size=20,
    replace=False
)

customers.loc[
    invalid_gender_indices,
    "gender"
] = "Unknown"


# Duplicate customers

duplicate_customers = customers.sample(
    20,
    random_state=SEED
)

customers = pd.concat(
    [customers, duplicate_customers],
    ignore_index=True
)


# ---------------------------------------
# ORDER DATA ISSUES
# ---------------------------------------

# Invalid customer IDs

invalid_order_customer_indices = np.random.choice(
    orders.index,
    size=30,
    replace=False
)

orders.loc[
    invalid_order_customer_indices,
    "customer_id"
] = "C999999"


# Negative quantity

negative_quantity_indices = np.random.choice(
    orders.index,
    size=20,
    replace=False
)

orders.loc[
    negative_quantity_indices,
    "quantity"
] = -1


# Zero quantity

zero_quantity_indices = np.random.choice(
    orders.index,
    size=20,
    replace=False
)

orders.loc[
    zero_quantity_indices,
    "quantity"
] = 0


# Negative amount

negative_amount_indices = np.random.choice(
    orders.index,
    size=20,
    replace=False
)

orders.loc[
    negative_amount_indices,
    "total_amount"
] = -100


# Duplicate orders

duplicate_orders = orders.sample(
    30,
    random_state=SEED
)

orders = pd.concat(
    [orders, duplicate_orders],
    ignore_index=True
)


# ---------------------------------------
# Save corrupted datasets
# ---------------------------------------

customers.to_csv(
    "data/corrupted/customers_corrupted.csv",
    index=False
)

orders.to_csv(
    "data/corrupted/orders_corrupted.csv",
    index=False
)


# ---------------------------------------
# Output
# ---------------------------------------

print("Data corruption completed!")

print(
    "Customers:",
    len(customers)
)

print(
    "Orders:",
    len(orders)
)