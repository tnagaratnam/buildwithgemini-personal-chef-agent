"""Firestore client and tool functions for Personal Chef agent."""

import json
from typing import Any
import google.auth
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-02-82ea50e03721"


def _get_firestore_client() -> firestore.Client:
    """Returns a Firestore client initialized with explicit project ID and scopes."""
    creds, _ = google.auth.default(
        scopes=[
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/datastore",
        ]
    )
    return firestore.Client(project=PROJECT_ID, credentials=creds)


def search_recipes(query: str = "", cuisine: str = "") -> str:
    """Searches recipes in the Firestore database by keyword or cuisine.

    Args:
        query: Optional search keyword to filter by title or dietary tags (e.g. 'pasta', 'vegan', 'chicken').
        cuisine: Optional cuisine filter (e.g. 'Italian', 'Indian', 'Asian Fusion').

    Returns:
        A string listing matching recipes with ID, title, cuisine, dietary tags, and prep time.
    """
    try:
        db = _get_firestore_client()
        docs = db.collection("recipes").stream()
        results = []

        query_lower = query.strip().lower()
        cuisine_lower = cuisine.strip().lower()

        for doc in docs:
            data = doc.to_dict()
            if not data:
                continue

            title = str(data.get("title", ""))
            recipe_cuisine = str(data.get("cuisine", ""))
            tags = [str(t).lower() for t in data.get("dietary_tags", [])]

            # Filter by cuisine if specified
            if cuisine_lower and cuisine_lower not in recipe_cuisine.lower():
                continue

            # Filter by query keyword if specified
            if query_lower:
                match_title = query_lower in title.lower()
                match_cuisine = query_lower in recipe_cuisine.lower()
                match_tags = any(query_lower in t for t in tags)
                if not (match_title or match_cuisine or match_tags):
                    continue

            results.append({
                "recipe_id": doc.id,
                "title": title,
                "cuisine": recipe_cuisine,
                "dietary_tags": data.get("dietary_tags", []),
                "prep_time_minutes": data.get("prep_time_minutes"),
                "cook_time_minutes": data.get("cook_time_minutes"),
                "calories_per_serving": data.get("calories_per_serving"),
            })

        if not results:
            return f"No recipes found matching query '{query}' and cuisine '{cuisine}'."

        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error searching recipes from Firestore: {str(e)}"


def get_recipe_by_id(recipe_id: str) -> str:
    """Fetches full details of a specific recipe from Firestore.

    Args:
        recipe_id: The unique identifier of the recipe document (e.g. 'recipe-001').

    Returns:
        A formatted string containing complete recipe details including ingredients and step-by-step instructions.
    """
    try:
        db = _get_firestore_client()
        doc_ref = db.collection("recipes").document(recipe_id)
        doc = doc_ref.get()

        if not doc.exists:
            return f"Recipe with ID '{recipe_id}' not found."

        data = doc.to_dict()
        data["recipe_id"] = doc.id
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error retrieving recipe '{recipe_id}' from Firestore: {str(e)}"


def add_recipe(
    recipe_id: str,
    title: str,
    cuisine: str,
    dietary_tags: list[str],
    prep_time_minutes: int,
    cook_time_minutes: int,
    servings: int,
    ingredients_json: str,
    instructions_json: str,
    calories_per_serving: int,
) -> str:
    """Adds or updates a recipe document in the Firestore database.

    Args:
        recipe_id: Unique identifier for the new recipe (e.g. 'recipe-004').
        title: Title of the dish (e.g. 'Vegetable Stir-Fry').
        cuisine: Cuisine classification (e.g. 'Chinese', 'Mexican').
        dietary_tags: List of dietary tags (e.g. ['vegan', 'quick']).
        prep_time_minutes: Preparation time in minutes.
        cook_time_minutes: Cooking time in minutes.
        servings: Number of servings.
        ingredients_json: JSON string of ingredients list, e.g. '[{"name": "Tofu", "amount": "200g"}]'.
        instructions_json: JSON string of cooking steps list, e.g. '["Step 1...", "Step 2..."]'.
        calories_per_serving: Calories count per serving.

    Returns:
        A confirmation string indicating successful creation/update.
    """
    try:
        db = _get_firestore_client()

        try:
            ingredients = json.loads(ingredients_json)
        except Exception:
            ingredients = [{"name": ingredients_json, "amount": "as required"}]

        try:
            instructions = json.loads(instructions_json)
        except Exception:
            instructions = [instructions_json]

        recipe_doc = {
            "recipe_id": recipe_id,
            "title": title,
            "cuisine": cuisine,
            "dietary_tags": dietary_tags,
            "prep_time_minutes": prep_time_minutes,
            "cook_time_minutes": cook_time_minutes,
            "servings": servings,
            "ingredients": ingredients,
            "instructions": instructions,
            "calories_per_serving": calories_per_serving,
        }

        db.collection("recipes").document(recipe_id).set(recipe_doc)
        return f"Successfully added recipe '{title}' (ID: {recipe_id}) to Firestore."
    except Exception as e:
        return f"Error adding recipe '{recipe_id}' to Firestore: {str(e)}"


def save_meal_plan(day_of_week: str, meal_type: str, recipe_id: str) -> str:
    """Saves a recipe to the user's weekly meal plan in Firestore.

    Args:
        day_of_week: Day of the week (e.g. 'Monday', 'Tuesday', 'Wednesday').
        meal_type: Type of meal (e.g. 'Breakfast', 'Lunch', 'Dinner').
        recipe_id: Unique identifier of the recipe to schedule (e.g. 'recipe-001').

    Returns:
        A confirmation string indicating successful scheduling.
    """
    try:
        db = _get_firestore_client()
        doc_id = f"{day_of_week.strip().lower()}_{meal_type.strip().lower()}"

        recipe_doc = db.collection("recipes").document(recipe_id).get()
        recipe_title = recipe_doc.to_dict().get("title", recipe_id) if recipe_doc.exists else recipe_id

        item = {
            "day_of_week": day_of_week.capitalize(),
            "meal_type": meal_type.capitalize(),
            "recipe_id": recipe_id,
            "recipe_title": recipe_title,
        }
        db.collection("meal_plan").document(doc_id).set(item)
        return f"Successfully scheduled '{recipe_title}' for {day_of_week.capitalize()} {meal_type.capitalize()}."
    except Exception as e:
        return f"Error saving meal plan: {str(e)}"


def get_meal_plan() -> str:
    """Retrieves the user's current weekly meal plan schedule from Firestore.

    Returns:
        A JSON string listing all scheduled meals for the week.
    """
    try:
        db = _get_firestore_client()
        docs = db.collection("meal_plan").stream()
        plan = [doc.to_dict() for doc in docs if doc.to_dict()]
        if not plan:
            return "No meals currently scheduled in the meal plan."
        return json.dumps(plan, indent=2)
    except Exception as e:
        return f"Error retrieving meal plan: {str(e)}"

