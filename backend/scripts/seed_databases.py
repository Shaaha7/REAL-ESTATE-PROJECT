"""One-off script: seeds MySQL (structured columns) and MongoDB (full documents,
with a text index) from the same property records, so PropertyRetrievalAgent has
real data to query instead of only ever falling back to the in-memory demo list.

Run from backend/: python scripts/seed_databases.py
"""
from __future__ import annotations
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents.property_retrieval_agent import DEMO_PROPERTIES
from src.database.mysql_client import MySQLClient
from src.database.mongo_client import MongoClient

# amenities/images are stored JSON-encoded so MySQL-routed results carry the same
# fields as MongoDB/demo ones - the frontend property card renders either way
MYSQL_COLUMNS = [
    "id", "title", "location", "price", "bedrooms", "bathrooms", "area_sqft",
    "property_type", "status", "yield_pct", "service_charge_yearly", "agent", "rera_no",
    "description", "amenities", "images",
]


def seed_mysql() -> int:
    client = MySQLClient()
    engine = client.engine
    if engine is None:
        print("MySQL: not reachable, skipped")
        return 0

    from sqlalchemy import text

    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS properties (
                id VARCHAR(16) PRIMARY KEY,
                title VARCHAR(255),
                location VARCHAR(128),
                price DOUBLE,
                bedrooms INT,
                bathrooms DOUBLE,
                area_sqft INT,
                property_type VARCHAR(64),
                status VARCHAR(32),
                yield_pct DOUBLE,
                service_charge_yearly DOUBLE,
                agent VARCHAR(128),
                rera_no VARCHAR(32),
                description TEXT,
                amenities TEXT,
                images TEXT
            )
        """))
        for p in DEMO_PROPERTIES:
            row = {k: p.get(k) for k in MYSQL_COLUMNS}
            row["amenities"] = json.dumps(p.get("amenities", []))
            row["images"] = json.dumps(p.get("images", []))
            placeholders = ", ".join(f":{k}" for k in MYSQL_COLUMNS)
            updates = ", ".join(f"{k}=VALUES({k})" for k in MYSQL_COLUMNS if k != "id")
            conn.execute(text(
                f"INSERT INTO properties ({', '.join(MYSQL_COLUMNS)}) VALUES ({placeholders}) "
                f"ON DUPLICATE KEY UPDATE {updates}"
            ), row)
        conn.commit()
    print(f"MySQL: seeded {len(DEMO_PROPERTIES)} rows into 'properties'")
    return len(DEMO_PROPERTIES)


def seed_mongo() -> int:
    client = MongoClient()
    db = client.db
    if db is None:
        print("MongoDB: not reachable, skipped")
        return 0

    coll = db["properties"]
    coll.create_index([("title", "text"), ("description", "text"), ("amenities", "text"), ("location", "text")])
    for p in DEMO_PROPERTIES:
        coll.replace_one({"id": p["id"]}, p, upsert=True)
    print(f"MongoDB: seeded {len(DEMO_PROPERTIES)} documents into 'properties' (+ text index)")
    return len(DEMO_PROPERTIES)


if __name__ == "__main__":
    mysql_count = seed_mysql()
    mongo_count = seed_mongo()
    if mysql_count == 0 and mongo_count == 0:
        print("\nNeither database was reachable - is docker compose up (mysql, mongo)?")
        sys.exit(1)
