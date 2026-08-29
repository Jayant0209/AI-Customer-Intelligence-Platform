import pandas as pd
import numpy as np
from faker import Faker
from datetime import date, timedelta

fake = Faker()

SEED = 42
REFERENCE_DATE = "2026-08-13"
NUM_CUSTOMERS = 10_000

np.random.seed(SEED)
fake.seed_instance(SEED)


customer_ids = [
    f"C{i:06d}"
    for i in range(1, NUM_CUSTOMERS + 1)
]


first_names = [
    fake.first_name()
    for _ in range(NUM_CUSTOMERS)
]


last_names = [
    fake.last_name()
    for _ in range(NUM_CUSTOMERS)
]


emails = [
    fake.email()
    for _ in range(NUM_CUSTOMERS)
]


genders = np.random.choice(
    ["Male", "Female"],
    size=NUM_CUSTOMERS,
    p=[0.55, 0.45]
)


cities = [
    "Delhi",
    "Jaipur",
    "Lucknow",
    "Mumbai",
    "Pune",
    "Bangalore",
    "Chennai",
    "Hyderabad",
    "Kolkata",
    "Bhubaneswar"
]


customer_cities = np.random.choice(
    cities,
    size=NUM_CUSTOMERS
)


city_to_state = {
    "Delhi": "Delhi",
    "Jaipur": "Rajasthan",
    "Lucknow": "Uttar Pradesh",
    "Mumbai": "Maharashtra",
    "Pune": "Maharashtra",
    "Bangalore": "Karnataka",
    "Chennai": "Tamil Nadu",
    "Hyderabad": "Telangana",
    "Kolkata": "West Bengal",
    "Bhubaneswar": "Odisha"
}


states = [
    city_to_state[city]
    for city in customer_cities
]


reference_date = date(2026, 8, 13)
start_date = reference_date - timedelta(days=365)

signup_dates = [
    fake.date_between(
        start_date=start_date,
        end_date=reference_date
    )
    for _ in range(NUM_CUSTOMERS)
]


customer_segments = np.random.choice(
    ["Premium", "Regular", "Budget"],
    size=NUM_CUSTOMERS,
    p=[0.15, 0.60, 0.25]
)


customers = pd.DataFrame({
    "customer_id": customer_ids,
    "first_name": first_names,
    "last_name": last_names,
    "email": emails,
    "gender": genders,
    "city": customer_cities,
    "state": states,
    "signup_date": signup_dates,
    "customer_segment": customer_segments
})


# Data quality checks

assert len(customers) == NUM_CUSTOMERS
assert customers["customer_id"].is_unique
assert customers["customer_id"].notna().all()
assert customers["email"].notna().all()


print("Customer data generated successfully!")
print("Number of customers:", len(customers))

print("\nCustomer data validation passed!")
print("Unique customers:", customers["customer_id"].nunique())
print("Missing customer IDs:", customers["customer_id"].isna().sum())
print("Missing emails:", customers["email"].isna().sum())

print("\nSample records:")
print(customers.head())


customers.to_csv(
    "data/raw/customers.csv",
    index=False
)