import pandas as pd
import numpy as np


SEED = 42
NUM_PAYMENTS = 100_000

np.random.seed(SEED)


# ---------------------------------------
# Load orders
# ---------------------------------------

orders = pd.read_csv(
    "data/raw/orders.csv"
)


# ---------------------------------------
# Generate payment IDs
# ---------------------------------------

payment_ids = [
    f"PAY{i:06d}"
    for i in range(1, NUM_PAYMENTS + 1)
]


# ---------------------------------------
# Get order IDs
# ---------------------------------------

order_ids = orders["order_id"].values


# ---------------------------------------
# Payment methods
# ---------------------------------------

payment_methods = np.random.choice(
    [
        "UPI",
        "CREDIT_CARD",
        "DEBIT_CARD",
        "NET_BANKING",
        "WALLET"
    ],
    size=NUM_PAYMENTS,
    p=[0.45, 0.25, 0.15, 0.10, 0.05]
)


# ---------------------------------------
# Payment statuses
# ---------------------------------------

payment_statuses = np.random.choice(
    [
        "SUCCESS",
        "FAILED",
        "REFUNDED",
        "PENDING"
    ],
    size=NUM_PAYMENTS,
    p=[0.88, 0.06, 0.04, 0.02]
)


# ---------------------------------------
# Payment amounts
# ---------------------------------------

amounts = orders["total_amount"].values


# ---------------------------------------
# Payment dates
# ---------------------------------------

order_dates = pd.to_datetime(
    orders["order_date"]
)

payment_dates = order_dates + pd.to_timedelta(
    np.random.randint(
        0,
        3,
        size=NUM_PAYMENTS
    ),
    unit="D"
)


# ---------------------------------------
# Create DataFrame
# ---------------------------------------

payments = pd.DataFrame({
    "payment_id": payment_ids,
    "order_id": order_ids,
    "payment_date": payment_dates,
    "payment_method": payment_methods,
    "payment_status": payment_statuses,
    "amount": amounts
})


# ---------------------------------------
# Data quality checks
# ---------------------------------------

assert len(payments) == NUM_PAYMENTS

assert payments["payment_id"].is_unique

assert payments["order_id"].isin(
    orders["order_id"]
).all()

assert (
    payments["amount"].values
    == orders["total_amount"].values
).all()

assert payments["amount"].gt(0).all()


# ---------------------------------------
# Save
# ---------------------------------------

payments.to_csv(
    "data/raw/payments.csv",
    index=False
)


# ---------------------------------------
# Output
# ---------------------------------------

print("Payment data generated successfully!")
print("Number of payments:", len(payments))

print("\nPayment validation passed!")

print("\nPayment status distribution:")
print(payments["payment_status"].value_counts())

print("\nPayment method distribution:")
print(payments["payment_method"].value_counts())

print("\nSample payments:")
print(payments.head())