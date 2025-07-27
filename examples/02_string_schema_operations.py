#!/usr/bin/env python3
"""
String-Schema Operations Example

This example demonstrates the power of string-schema operations:
- Schema validation and type safety
- Custom schema definitions
- JSON field handling
- Complex filtering with schema validation
- Performance considerations

String-schema operations are perfect for APIs and data validation!
"""

from simple_sqlalchemy import DbClient, CommonBase, BaseCrud
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON, Float
from datetime import datetime, date
import json


# Setup
print("=== String-Schema Operations Demo ===")
import os
import time
# Use a unique database name to avoid conflicts
db_name = f"schema_demo_{int(time.time())}.db"
db = DbClient(f"sqlite:///{db_name}")
print(f"✅ Connected to database: {db_name}")


# Define Models with Various Field Types
class Product(CommonBase):
    __tablename__ = 'products'

    name = Column(String(100), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category = Column(String(50))
    in_stock = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    product_metadata = Column(JSON, default=lambda: {})  # JSON field (renamed to avoid conflict)
    tags = Column(JSON, default=lambda: [])      # JSON array

CommonBase.metadata.create_all(db.engine)
product_crud = BaseCrud(Product, db)


# 1. Schema Type Mapping
print("\n=== 1. Schema Type Mapping ===")

# Create sample products with various data types
products_data = [
    {
        "name": "Laptop Pro",
        "description": "High-performance laptop for professionals",
        "price": 1299.99,
        "category": "Electronics",
        "in_stock": True,
        "product_metadata": {"brand": "TechCorp", "warranty": "2 years", "specs": {"ram": "16GB", "storage": "512GB"}},
        "tags": ["laptop", "professional", "high-performance"]
    },
    {
        "name": "Coffee Mug",
        "description": "Ceramic coffee mug with company logo",
        "price": 12.50,
        "category": "Office",
        "in_stock": True,
        "product_metadata": {"material": "ceramic", "capacity": "350ml"},
        "tags": ["mug", "coffee", "office"]
    },
    {
        "name": "Wireless Mouse",
        "description": "Ergonomic wireless mouse",
        "price": 45.00,
        "category": "Electronics",
        "in_stock": False,
        "product_metadata": {"connectivity": "bluetooth", "battery": "rechargeable"},
        "tags": ["mouse", "wireless", "ergonomic"]
    }
]

created_ids = []
for product_data in products_data:
    product_id = product_crud.create(product_data)
    created_ids.append(product_id)

print(f"✅ Created {len(created_ids)} products")


# 2. Basic Schema Queries
print("\n=== 2. Basic Schema Queries ===")

# Query with different field types
all_products = product_crud.query_with_schema(
    schema_str="id:int, name:string, price:float, in_stock:bool, created_at:datetime",
    sort_by="price"
)

print("All products with basic schema:")
for product in all_products:
    print(f"  - {product['name']}: ${product['price']:.2f} (Stock: {product['in_stock']}) - Created: {product['created_at']}")


# 3. JSON Field Handling
print("\n=== 3. JSON Field Handling ===")

# JSON fields are serialized as strings for schema validation
products_with_json = product_crud.query_with_schema(
    schema_str="id:int, name:string, product_metadata:string, tags:string",
    filters={"category": "Electronics"}
)

print("Electronics with JSON data:")
for product in products_with_json:
    # Parse JSON strings back to objects
    metadata = json.loads(product['product_metadata']) if product['product_metadata'] else {}
    tags = json.loads(product['tags']) if product['tags'] else []

    print(f"  - {product['name']}")
    print(f"    Metadata: {metadata}")
    print(f"    Tags: {tags}")


# 4. Custom Schema Definitions
print("\n=== 4. Custom Schema Definitions ===")

# Define reusable schemas
product_crud.add_schema("basic", "id:int, name:string, price:float")
product_crud.add_schema("full", "id:int, name:string, description:text?, price:float, category:string?, in_stock:bool")
product_crud.add_schema("api", "id:int, name:string, price:float, in_stock:bool, category:string?")

# Use predefined schemas
basic_products = product_crud.query_with_schema("basic", limit=2)
print("Products with 'basic' schema:")
for product in basic_products:
    print(f"  - {product['name']}: ${product['price']:.2f}")

full_products = product_crud.query_with_schema("full", filters={"in_stock": True})
print(f"\nIn-stock products with 'full' schema ({len(full_products)}):")
for product in full_products:
    desc = product['description'][:50] + "..." if product['description'] and len(product['description']) > 50 else product['description']
    print(f"  - {product['name']} ({product['category']}): {desc}")


# 5. Advanced Filtering with Schema
print("\n=== 5. Advanced Filtering with Schema ===")

# Complex filters with schema validation
filtered_products = product_crud.query_with_schema(
    schema_str="id:int, name:string, price:float, category:string?, in_stock:bool",
    filters={
        "price": {">=": 20.0, "<=": 1000.0},     # Price range
        "category": ["Electronics", "Office"],    # Multiple categories
        "in_stock": {"not": None},               # Has stock status
        "name": {"ilike": "%o%"}                 # Name contains 'o' (case-insensitive)
    },
    sort_by="price",
    sort_desc=True
)

print("Filtered products (price $20-$1000, Electronics/Office, name contains 'o'):")
for product in filtered_products:
    print(f"  - {product['name']} ({product['category']}): ${product['price']:.2f} - Stock: {product['in_stock']}")


# 6. Pagination with Schema
print("\n=== 6. Pagination with Schema ===")

paginated_result = product_crud.paginated_query_with_schema(
    schema_str="id:int, name:string, price:float, category:string?",
    page=1,
    per_page=2,
    filters={"in_stock": True},
    sort_by="name"
)

print("Paginated products (page 1, 2 per page):")
print(f"  Total: {paginated_result['total']}")
print(f"  Pages: {paginated_result['total_pages']}")
print(f"  Has next: {paginated_result['has_next']}")
print("  Items:")
for product in paginated_result['items']:
    print(f"    - {product['name']} ({product['category']}): ${product['price']:.2f}")


# 7. Search with Schema
print("\n=== 7. Search with Schema ===")

search_results = product_crud.query_with_schema(
    schema_str="id:int, name:string, description:text?, category:string?",
    search_query="laptop",
    search_fields=["name", "description"],
    filters={"in_stock": True}
)

print("Search results for 'laptop':")
for product in search_results:
    print(f"  - {product['name']} ({product['category']})")
    if product['description']:
        print(f"    Description: {product['description'][:100]}...")


# 8. Aggregation with Schema
print("\n=== 8. Aggregation with Schema ===")

category_stats = product_crud.aggregate_with_schema(
    aggregations={
        "count": "count(id)",
        "avg_price": "avg(price)",
        "max_price": "max(price)",
        "min_price": "min(price)"
    },
    schema_str="category:string?, count:int, avg_price:float?, max_price:float?, min_price:float?",
    group_by=["category"],
    filters={"price": {">=": 0}}  # Valid prices only
)

print("Product statistics by category:")
for stat in category_stats:
    category = stat['category'] or 'No Category'
    print(f"  - {category}:")
    print(f"    Count: {stat['count']}")
    print(f"    Price range: ${stat['min_price']:.2f} - ${stat['max_price']:.2f}")
    print(f"    Average price: ${stat['avg_price']:.2f}")


# 9. CRUD with Return Schemas
print("\n=== 9. CRUD with Return Schemas ===")

# Create and get data back with schema
new_product_id = product_crud.create({
    "name": "Smartphone",
    "description": "Latest model smartphone",
    "price": 699.99,
    "category": "Electronics",
    "product_metadata": {"brand": "PhoneCorp", "storage": "128GB"},
    "tags": ["phone", "smartphone", "mobile"]
})

# Get the created product with schema
new_product = product_crud.query_with_schema(
    "id:int, name:string, price:float, created_at:datetime",
    filters={"id": new_product_id.id if hasattr(new_product_id, 'id') else new_product_id}
)[0]

print("Created product with schema:")
print(f"  - {new_product['name']} (ID: {new_product['id']}): ${new_product['price']:.2f}")
print(f"    Created at: {new_product['created_at']}")

# Update and get data back with schema
actual_id = new_product_id.id if hasattr(new_product_id, 'id') else new_product_id
product_crud.update(actual_id, {"price": 649.99, "in_stock": True})

# Get the updated product with schema
updated_product = product_crud.query_with_schema(
    "id:int, name:string, price:float, in_stock:bool",
    filters={"id": actual_id}
)[0]

print("Updated product with schema:")
print(f"  - {updated_product['name']}: ${updated_product['price']:.2f} (Stock: {updated_product['in_stock']})")


# 10. Fetch One and Scalar Operations (90% Use Case)
print("\n=== 10. Fetch One and Scalar Operations ===")

# Get a single product by ID
single_product = product_crud.get_one_with_schema(
    "id:int, name:string, price:float, category:string?",
    filters={"id": created_ids[0].id if hasattr(created_ids[0], 'id') else created_ids[0]}
)

if single_product:
    print(f"Single product: {single_product['name']} - ${single_product['price']:.2f}")

# Get the most expensive product
expensive_product = product_crud.get_one_with_schema(
    "id:int, name:string, price:float",
    sort_by="price",
    sort_desc=True
)

if expensive_product:
    print(f"Most expensive: {expensive_product['name']} - ${expensive_product['price']:.2f}")

# Get scalar values
product_count = product_crud.get_scalar_with_schema("count(*)")
print(f"Total products: {product_count}")

avg_price = product_crud.get_scalar_with_schema("avg(price)")
print(f"Average price: ${avg_price:.2f}")

max_price = product_crud.get_scalar_with_schema("max(price)")
print(f"Highest price: ${max_price:.2f}")

# Get a specific field value
laptop_name = product_crud.get_scalar_with_schema(
    "name",
    filters={"category": "Electronics", "name": {"like": "%Laptop%"}}
)
print(f"Laptop product name: {laptop_name}")

# Count products by category
electronics_count = product_crud.get_scalar_with_schema(
    "count(*)",
    filters={"category": "Electronics"}
)
print(f"Electronics products: {electronics_count}")


# 11. Schema Validation Benefits
print("\n=== 10. Schema Validation Benefits ===")

print("✅ Type Safety: All fields are validated according to schema")
print("✅ API Ready: Results are JSON-serializable dictionaries")
print("✅ Consistent: Same data structure every time")
print("✅ Flexible: Define custom schemas for different use cases")
print("✅ Performance: Only fetch the fields you need")
print("✅ Documentation: Schema serves as field documentation")

print("\n🎉 String-Schema Operations Complete!")
print("\nKey takeaways:")
print("- Use string-schema for API endpoints and data validation")
print("- JSON fields are serialized as strings (parse with json.loads)")
print("- Define reusable schemas for different contexts")
print("- Schema validation ensures type safety and consistency")
print("- Perfect for web APIs and microservices!")

# Cleanup
print(f"\n🧹 Cleaning up database file: {db_name}")
try:
    os.remove(db_name)
    print("✅ Database file removed")
except:
    print("⚠️ Could not remove database file")
