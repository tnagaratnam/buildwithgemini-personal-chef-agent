#!/usr/bin/env python3
"""Seed script for populating the Firestore 'recipes' collection."""

import google.auth
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-02-82ea50e03721"

SEED_RECIPES = [
    {
        "recipe_id": "recipe-001",
        "title": "Creamy Garlic Parmesan Pasta",
        "cuisine": "Italian",
        "dietary_tags": ["vegetarian"],
        "prep_time_minutes": 10,
        "cook_time_minutes": 15,
        "servings": 4,
        "ingredients": [
            {"name": "Fettuccine or Penne", "amount": "400g"},
            {"name": "Heavy Cream", "amount": "1 cup"},
            {"name": "Grated Parmesan Cheese", "amount": "1 cup"},
            {"name": "Garlic (minced)", "amount": "4 cloves"},
            {"name": "Butter", "amount": "2 tbsp"},
            {"name": "Salt & Fresh Black Pepper", "amount": "to taste"},
            {"name": "Fresh Parsley (chopped)", "amount": "2 tbsp"},
        ],
        "instructions": [
            "Boil pasta in salted water until al dente.",
            "In a large skillet, melt butter over medium heat and sauté minced garlic for 1 minute until fragrant.",
            "Pour in heavy cream and bring to a simmer. Reduce heat to low.",
            "Stir in grated Parmesan cheese until melted and smooth sauce forms.",
            "Toss cooked pasta into sauce, sprinkle with chopped parsley, salt, and black pepper, then serve warm.",
        ],
        "calories_per_serving": 520,
        "image_url": "https://storage.googleapis.com/static-assets/garlic_pasta.jpg",
    },
    {
        "recipe_id": "recipe-002",
        "title": "Chicken Tikka Masala",
        "cuisine": "Indian",
        "dietary_tags": ["gluten-free", "high-protein"],
        "prep_time_minutes": 20,
        "cook_time_minutes": 25,
        "servings": 4,
        "ingredients": [
            {"name": "Boneless Chicken Thighs (cubed)", "amount": "600g"},
            {"name": "Plain Yogurt", "amount": "1/2 cup"},
            {"name": "Garam Masala", "amount": "2 tbsp"},
            {"name": "Tomato Purée", "amount": "1.5 cups"},
            {"name": "Heavy Cream or Coconut Milk", "amount": "1/2 cup"},
            {"name": "Onion (finely diced)", "amount": "1 large"},
            {"name": "Garlic & Ginger Paste", "amount": "1 tbsp"},
        ],
        "instructions": [
            "Marinate chicken in yogurt and spices for at least 15 minutes.",
            "Sear chicken pieces in a hot skillet until golden brown; set aside.",
            "In the same pan, cook diced onions, ginger, and garlic paste until golden.",
            "Add tomato purée and simmer for 10 minutes until sauce thickens.",
            "Stir in heavy cream and cooked chicken. Simmer for 5 minutes until chicken is cooked through.",
        ],
        "calories_per_serving": 480,
        "image_url": "https://storage.googleapis.com/static-assets/tikka_masala.jpg",
    },
    {
        "recipe_id": "recipe-003",
        "title": "Tofu & Quinoa Buddha Bowl",
        "cuisine": "Asian Fusion",
        "dietary_tags": ["vegan", "gluten-free", "healthy"],
        "prep_time_minutes": 15,
        "cook_time_minutes": 20,
        "servings": 2,
        "ingredients": [
            {"name": "Extra Firm Tofu (cubed)", "amount": "250g"},
            {"name": "Cooked Quinoa", "amount": "1.5 cups"},
            {"name": "Roasted Sweet Potato", "amount": "1 cup"},
            {"name": "Fresh Spinach / Kale", "amount": "2 cups"},
            {"name": "Tahini Dressing", "amount": "3 tbsp"},
            {"name": "Sesame Seeds", "amount": "1 tbsp"},
        ],
        "instructions": [
            "Pan-fry cubed tofu with a dash of soy sauce and sesame oil until crispy.",
            "Divide cooked quinoa into two serving bowls as the base.",
            "Arrange crispy tofu, roasted sweet potato cubes, and fresh greens on top.",
            "Drizzle generously with tahini dressing and sprinkle with sesame seeds.",
        ],
        "calories_per_serving": 410,
        "image_url": "https://storage.googleapis.com/static-assets/buddha_bowl.jpg",
    },
]


def seed_database():
    """Seeds the Firestore database with sample recipe documents."""
    print(f"Connecting to Firestore for project '{PROJECT_ID}'...")
    creds, _ = google.auth.default(
        scopes=[
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/datastore",
        ]
    )
    db = firestore.Client(project=PROJECT_ID, credentials=creds)
    collection_ref = db.collection("recipes")

    for recipe in SEED_RECIPES:
        doc_id = recipe["recipe_id"]
        collection_ref.document(doc_id).set(recipe)
        print(f"  [+] Seeded recipe document: {doc_id} -> '{recipe['title']}'")

    print("\nSuccessfully seeded Firestore 'recipes' collection!")


if __name__ == "__main__":
    seed_database()
