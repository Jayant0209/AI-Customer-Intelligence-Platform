import pandas as pd
import numpy as np
from faker import Faker

fake = Faker()

SEED = 42
NUM_PRODUCTS = 1_000

np.random.seed(SEED)
fake.seed_instance(SEED)


category_map = {
    "Electronics": [
        "Mobile",
        "Laptop",
        "Audio",
        "Accessories"
    ],
    "Fashion": [
        "Men",
        "Women",
        "Footwear",
        "Accessories"
    ],
    "Home & Kitchen": [
        "Kitchen",
        "Furniture",
        "Appliances"
    ],
    "Beauty": [
        "Skincare",
        "Makeup",
        "Haircare"
    ],
    "Sports": [
        "Fitness",
        "Outdoor",
        "Sportswear"
    ],
    "Books": [
        "Fiction",
        "Non-Fiction",
        "Education"
    ]
}


brands = [
    "NovaTech",
    "UrbanStyle",
    "HomePro",
    "FitLife",
    "GlowCare",
    "BookWorld",
    "SoundMax",
    "SmartGear"
]


product_ids = [
    f"P{i:06d}"
    for i in range(1, NUM_PRODUCTS + 1)
]


categories = np.random.choice(
    list(category_map.keys()),
    size=NUM_PRODUCTS
)


subcategories = [
    np.random.choice(category_map[category])
    for category in categories
]


product_names = [
    fake.catch_phrase()
    for _ in range(NUM_PRODUCTS)
]


product_brands = np.random.choice(
    brands,
    size=NUM_PRODUCTS
)


prices = np.random.randint(
    299,
    100_000,
    size=NUM_PRODUCTS
)


costs = [
    round(price * np.random.uniform(0.50, 0.85), 2)
    for price in prices
]


products = pd.DataFrame({
    "product_id": product_ids,
    "product_name": product_names,
    "category": categories,
    "subcategory": subcategories,
    "brand": product_brands,
    "price": prices,
    "cost": costs
})


# Data quality checks

assert len(products) == NUM_PRODUCTS
assert products["product_id"].is_unique
assert products["product_id"].notna().all()
assert products["price"].gt(0).all()
assert products["cost"].gt(0).all()
assert (products["cost"] < products["price"]).all()


products.to_csv(
    "data/raw/products.csv",
    index=False
)


print("Product data generated successfully!")
print("Number of products:", len(products))

print("\nProduct validation passed!")

print("\nCategory distribution:")
print(products["category"].value_counts())

print("\nSample products:")
print(products.head())