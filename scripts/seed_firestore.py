"""Seed Firestore database with initial destination items for Travel Concierge Agent."""

import os
from google.cloud import firestore

# IMPORTANT: Hardcode project ID as string for Firestore client.
# Do NOT use google.auth.default() or GOOGLE_CLOUD_PROJECT env var.
PROJECT_ID = "qwiklabs-gcp-01-1a01cf2a0844"

INITIAL_DESTINATIONS = [
    {
        "id": "paris",
        "name": "Paris",
        "country": "France",
        "category": "Culture & Cuisine",
        "best_season": "Spring & Autumn",
        "avg_daily_budget_usd": 250.0,
        "description": "Romantic capital known for art museums, iconic architecture, fashion, and gastronomy.",
        "rating": 4.8,
    },
    {
        "id": "tokyo",
        "name": "Tokyo",
        "country": "Japan",
        "category": "Modern & Tech",
        "best_season": "Spring & Autumn",
        "avg_daily_budget_usd": 200.0,
        "description": "Ultra-modern metropolis blending neon skyscrapers, historic temples, and world-class street food.",
        "rating": 4.9,
    },
    {
        "id": "kyoto",
        "name": "Kyoto",
        "country": "Japan",
        "category": "Culture & Heritage",
        "best_season": "Spring & Autumn",
        "avg_daily_budget_usd": 180.0,
        "description": "Cultural heart of Japan famous for classical Zen temples, traditional wooden houses, and bamboo groves.",
        "rating": 4.9,
    },
    {
        "id": "rio",
        "name": "Rio de Janeiro",
        "country": "Brazil",
        "category": "Beach & Nature",
        "best_season": "Summer (Dec-Mar)",
        "avg_daily_budget_usd": 140.0,
        "description": "Vibrant coastal city famed for Copacabana beach, Christ the Redeemer statue, and Carnival culture.",
        "rating": 4.6,
    },
    {
        "id": "san-francisco",
        "name": "San Francisco",
        "country": "USA",
        "category": "Coastal & Sightseeing",
        "best_season": "Autumn & Summer",
        "avg_daily_budget_usd": 220.0,
        "description": "Iconic California bay area city featuring the Golden Gate Bridge, historic cable cars, and tech hubs.",
        "rating": 4.7,
    },
]

def seed_database():
    print(f"Connecting to Firestore for project '{PROJECT_ID}'...")
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection("destinations")

    for dest in INITIAL_DESTINATIONS:
        dest_id = dest["id"]
        doc_ref = collection_ref.document(dest_id)
        doc_ref.set(dest)
        print(f"  ✓ Seeded destination: {dest['name']} ({dest_id})")

    print("\n✅ Firestore seeding complete!")

if __name__ == "__main__":
    seed_database()
