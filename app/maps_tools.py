"""Google Maps Geocoding and Places (New) function tools for Personal Chef agent."""

import json
import os
import urllib.parse
import urllib.request


def geocode_address(address: str) -> str:
    """Converts a street address or location name into geographic coordinates (latitude and longitude).

    Args:
        address: The address or location string (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA').

    Returns:
        JSON string containing the formatted address, latitude, and longitude.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY is not set in environment."

    encoded_address = urllib.parse.quote(address.strip())
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("status") != "OK" or not data.get("results"):
            return f"Geocoding failed for address '{address}': {data.get('status')}"

        result = data["results"][0]
        formatted_address = result.get("formatted_address")
        location = result.get("geometry", {}).get("location", {})

        output = {
            "formatted_address": formatted_address,
            "latitude": location.get("lat"),
            "longitude": location.get("lng"),
        }
        return json.dumps(output, indent=2)
    except Exception as e:
        return f"Error performing geocoding: {str(e)}"


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "supermarket",
    radius_meters: float = 3000.0,
) -> str:
    """Finds nearby places of a given type around coordinates using Places API (New).

    Args:
        latitude: Latitude of center search location (e.g. 37.4220).
        longitude: Longitude of center search location (e.g. -122.0841).
        place_type: Type of place to search for (e.g. 'supermarket', 'grocery_store', 'restaurant', 'bakery').
        radius_meters: Radius in meters for search area (default: 3000.0).

    Returns:
        JSON string listing nearby places with name, address, and location coordinates.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY is not set in environment."

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
    }

    body = {
        "includedTypes": [place_type.strip().lower()],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                },
                "radius": float(radius_meters),
            }
        },
    }

    try:
        data_bytes = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")

        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))

        places = res_data.get("places", [])
        if not places:
            return f"No nearby places of type '{place_type}' found within {radius_meters}m."

        results = []
        for p in places:
            display_name = p.get("displayName", {}).get("text") if isinstance(p.get("displayName"), dict) else p.get("displayName")
            results.append({
                "name": display_name,
                "address": p.get("formattedAddress"),
                "location": p.get("location"),
            })

        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error finding nearby places: {str(e)}"
