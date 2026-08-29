import pandas as pd
import numpy as np

SEED = 42
NUM_ORDERS = 100_000

np.random.seed(SEED)


# ---------------------------------------
# Load existing customer and product data
# ---------------------------------------

customers = pd.read_csv(
    "data/raw/customers.csv"
)

products = pd.read_csv(
    "data/raw/products.csv"
)


# ---------------------------------------
# Generate order IDs
# ---------------------------------------

order_ids = [
    f"O{i:06d}"
    for i in range(1, NUM_ORDERS + 1)
]


# ---------------------------------------
# Select customers and products
# ---------------------------------------

customer_ids = np.random.choice(
    customers["customer_id"],
    size=NUM_ORDERS
)

product_ids = np.random.choice(
    products["product_id"],
    size=NUM_ORDERS
)


# ---------------------------------------
# Get product prices
# ---------------------------------------

product_price_map = products.set_index(
    "product_id"
)["price"]

unit_prices = [
    product_price_map[product_id]
    for product_id in product_ids
]


# ---------------------------------------
# Generate order dates
# ---------------------------------------

order_dates = pd.date_range(
    start="2025-08-13",
    end="2026-08-13",
    periods=NUM_ORDERS
)


# ---------------------------------------
# Generate quantities
# ---------------------------------------

quantities = np.random.choice(
    [1, 2, 3, 4, 5],
    size=NUM_ORDERS,
    p=[0.55, 0.25, 0.12, 0.06, 0.02]
)


# ---------------------------------------
# Generate discounts
# ---------------------------------------

discount_percentages = np.random.choice(
    [0, 5, 10, 15, 20],
    size=NUM_ORDERS,
    p=[0.30, 0.30, 0.20, 0.15, 0.05]
)


discounts = (
    np.array(unit_prices)
    * quantities
    * discount_percentages
    / 100
)


# ---------------------------------------
# Calculate total amount
# ---------------------------------------

total_amounts = (
    np.array(unit_prices) * quantities
    - discounts
)


# ---------------------------------------
# Order status
# ---------------------------------------

order_statuses = np.random.choice(
    [
        "COMPLETED",
        "CANCELLED",
        "RETURNED",
        "PENDING"
    ],
    size=NUM_ORDERS,
    p=[0.85, 0.05, 0.07, 0.03]
)


# ---------------------------------------
# Region
# ---------------------------------------

customer_region_map = {
    "Delhi": "North",
    "Jaipur": "North",
    "Lucknow": "North",
    "Mumbai": "West",
    "Pune": "West",
    "Bangalore": "South",
    "Chennai": "South",
    "Hyderabad": "South",
    "Kolkata": "East",
    "Bhubaneswar": "East"
}


customer_city_map = customers.set_index(
    "customer_id"
)["city"]

cities = [
    customer_city_map[customer_id]
    for customer_id in customer_ids
]

regions = [
    customer_region_map[city]
    for city in cities
]


# ---------------------------------------
# Create DataFrame
# ---------------------------------------

orders = pd.DataFrame({
    "order_id": order_ids,
    "customer_id": customer_ids,
    "product_id": product_ids,
    "order_date": order_dates,
    "quantity": quantities,
    "unit_price": unit_prices,
    "discount": discounts.round(2),
    "total_amount": total_amounts.round(2),
    "order_status": order_statuses,
    "region": regions
})


# ---------------------------------------
# Data quality checks
# ---------------------------------------

assert len(orders) == NUM_ORDERS

assert orders["order_id"].is_unique

assert orders["customer_id"].isin(
    customers["customer_id"]
).all()

assert orders["product_id"].isin(
    products["product_id"]
).all()

assert orders["quantity"].gt(0).all()

assert orders["unit_price"].gt(0).all()

assert orders["total_amount"].ge(0).all()


# ---------------------------------------
# Save
# ---------------------------------------

orders.to_csv(
    "data/raw/orders.csv",
    index=False
)


# ---------------------------------------
# Output
# ---------------------------------------

print("Order data generated successfully!")

print("Number of orders:", len(orders))

print("\nOrder validation passed!")

print("\nOrder status distribution:")
print(orders["order_status"].value_counts())

print("\nSample orders:")
print(orders.head())