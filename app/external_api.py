"""External API tools for Personal Chef agent using TheMealDB free public API."""

import json
import os
import urllib.parse
import urllib.request


def fetch_external_recipes(query: str = "") -> str:
    """Fetches real recipe suggestions from TheMealDB public web API.

    Args:
        query: Optional dish or ingredient keyword to search for (e.g. 'chicken', 'pasta', 'tacos').
               If empty, fetches a random recipe inspiration.

    Returns:
        JSON string of matching recipes with title, category, cuisine origin, ingredients, and instructions.
    """
    api_key = os.getenv("THEMEALDB_API_KEY", "1")
    query_clean = query.strip()

    if query_clean:
        encoded_query = urllib.parse.quote(query_clean)
        url = f"https://www.themealdb.com/api/json/v1/{api_key}/search.php?s={encoded_query}"
    else:
        url = f"https://www.themealdb.com/api/json/v1/{api_key}/random.php"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "PersonalChefAgent/1.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status != 200:
                return f"Error: TheMealDB API returned status code {response.status}."
            raw_data = response.read().decode("utf-8")
            data = json.loads(raw_data)

        meals = data.get("meals")
        if not meals:
            return f"No external recipes found on TheMealDB for '{query_clean}'."

        formatted_meals = []
        for meal in meals[:3]:  # Limit to top 3
            # Extract non-empty ingredients and measurements
            ingredients = []
            for i in range(1, 21):
                ing = meal.get(f"strIngredient{i}")
                meas = meal.get(f"strMeasure{i}")
                if ing and ing.strip():
                    measure_str = meas.strip() if meas else ""
                    ingredients.append(f"{measure_str} {ing.strip()}".strip())

            formatted_meals.append({
                "meal_id": meal.get("idMeal"),
                "title": meal.get("strMeal"),
                "category": meal.get("strCategory"),
                "area_cuisine": meal.get("strArea"),
                "instructions": meal.get("strInstructions"),
                "ingredients": ingredients,
                "thumbnail_url": meal.get("strMealThumb"),
            })

        return json.dumps(formatted_meals, indent=2)
    except Exception as e:
        return f"Error fetching recipe from TheMealDB API: {str(e)}"
