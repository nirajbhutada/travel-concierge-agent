# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import os
from pathlib import Path
from typing import Optional
import urllib.parse
import urllib.request
import uuid
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from google import genai
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.cloud import firestore, storage
from google.genai import types
from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager

from .a2ui_utils import a2ui_callback

load_dotenv()

# Hardcode GCP project ID and bucket name as strings per requirements
PROJECT_ID = "qwiklabs-gcp-01-1a01cf2a0844"
BUCKET_NAME = "travel-concierge-assets-qwiklabs-gcp-01-1a01cf2a0844"

firestore_db = firestore.Client(project=PROJECT_ID)
storage_client = storage.Client(project=PROJECT_ID)


async def generate_destination_image(prompt: str, tool_context: ToolContext) -> str:
    """Generates an image for a destination or travel item using gemini-3.1-flash-lite-image in the global region.
    Saves the image as a session artifact for the Playground's Artifacts panel, uploads it to public Cloud Storage,
    and returns its public https URL.

    Args:
        prompt: Detailed description of the travel destination or postcard image to generate (e.g., 'A scenic view of Kyoto cherry blossoms in spring').
        tool_context: Tool context passed by the ADK framework.

    Returns:
        The public Cloud Storage https URL of the generated image.
    """
    try:
        genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")

        response = genai_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=f"Generate a high quality travel photograph or postcard: {prompt}",
        )

        image_bytes = None
        mime_type = "image/jpeg"

        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    image_bytes = part.inline_data.data
                    mime_type = part.inline_data.mime_type or "image/jpeg"
                    break

        if not image_bytes:
            return "Failed to generate image bytes from the model."

        filename = f"destination_{uuid.uuid4().hex[:8]}.jpg"

        # 1. Save artifact for Playground Artifacts panel
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload image bytes to public GCS bucket
        bucket = storage_client.bucket(BUCKET_NAME)
        blob_name = f"generated_images/{filename}"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_name}"
        return f"Successfully generated destination image!\nPublic URL: {public_url}"
    except Exception as e:
        return f"Error generating destination image: {e}"


async def generate_destination_video(prompt: str, tool_context: ToolContext) -> str:
    """Generates a short travel video clip for a destination using gemini-omni-flash-preview in the global region.
    Saves the video as a session artifact for the Playground's Artifacts panel, uploads it to public Cloud Storage,
    and returns its public https URL.

    Args:
        prompt: Detailed description of the travel destination video to generate (e.g., 'A short video clip of Kyoto cherry blossoms swaying in the breeze').
        tool_context: Tool context passed by the ADK framework.

    Returns:
        The public Cloud Storage https URL of the generated video.
    """
    try:
        genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")

        response = genai_client.models.generate_content(
            model="gemini-omni-flash-preview",
            contents=f"Generate a short high quality travel video clip: {prompt}",
        )

        video_bytes = None
        mime_type = "video/mp4"

        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    video_bytes = part.inline_data.data
                    mime_type = part.inline_data.mime_type or "video/mp4"
                    break

        if not video_bytes:
            return "Failed to generate video bytes from the model."

        filename = f"destination_video_{uuid.uuid4().hex[:8]}.mp4"

        # 1. Save artifact for Playground Artifacts panel
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload video bytes to public GCS bucket
        bucket = storage_client.bucket(BUCKET_NAME)
        blob_name = f"generated_videos/{filename}"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_name}"
        return f"Successfully generated destination video!\nPublic URL: {public_url}"
    except Exception as e:
        return f"Error generating destination video: {e}"



def geocode_address(address: str) -> str:
    """Uses the Google Geocoding API to convert an address or location name into geographic coordinates (latitude, longitude).

    Args:
        address: Address or landmark name (e.g., '1600 Amphitheatre Pkwy, Mountain View, CA' or 'Tokyo Station').

    Returns:
        String with formatted address, latitude, and longitude.
    """
    try:
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not api_key:
            return "Error: GOOGLE_MAPS_API_KEY environment variable is not set."

        query = urllib.parse.quote(address.strip())
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={query}&key={api_key}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("status") != "OK" or not data.get("results"):
            return f"Geocoding failed for address '{address}': {data.get('status', 'ZERO_RESULTS')}"

        result = data["results"][0]
        formatted_address = result.get("formatted_address", address)
        loc = result["geometry"]["location"]
        lat, lng = loc["lat"], loc["lng"]

        return f"Location: {formatted_address}\nCoordinates: Latitude {lat:.6f}, Longitude {lng:.6f}"
    except Exception as e:
        return f"Error calling Geocoding API: {e}"


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "tourist_attraction",
    radius_meters: float = 3000.0,
) -> str:
    """Uses the Google Places API (New) to search for nearby places of a given type around a latitude/longitude center.

    Args:
        latitude: Latitude coordinate of search center (e.g. 35.6812).
        longitude: Longitude coordinate of search center (e.g. 139.7671).
        place_type: Type of place to search for (e.g. 'tourist_attraction', 'restaurant', 'hotel', 'museum', 'park').
        radius_meters: Search radius in meters (default 3000.0).

    Returns:
        Formatted summary of nearby places containing name, formatted address, and coordinates.
    """
    try:
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not api_key:
            return "Error: GOOGLE_MAPS_API_KEY environment variable is not set."

        url = "https://places.googleapis.com/v1/places:searchNearby"
        payload = json.dumps(
            {
                "includedTypes": [place_type.strip().lower()],
                "maxResultCount": 5,
                "locationRestriction": {
                    "circle": {
                        "center": {"latitude": latitude, "longitude": longitude},
                        "radius": float(radius_meters),
                    }
                },
            }
        ).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.types",
        }

        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        places = data.get("places", [])
        if not places:
            return f"No nearby places of type '{place_type}' found within {radius_meters}m."

        results = []
        for place in places:
            display_name = place.get("displayName", {}).get("text", "Unknown Place")
            address = place.get("formattedAddress", "No address")
            location = place.get("location", {})
            lat = location.get("latitude", 0.0)
            lng = location.get("longitude", 0.0)
            results.append(f"- Name: {display_name}\n  Address: {address}\n  Location: Lat {lat:.6f}, Lng {lng:.6f}")

        return f"Found {len(results)} nearby '{place_type}' places:\n" + "\n".join(results)
    except Exception as e:
        return f"Error calling Places API (New): {e}"


def fetch_destination_summary(location: str) -> str:
    """Fetches real-time summary details and description for a travel destination or landmark from Wikipedia.

    Args:
        location: City, destination, or landmark name (e.g. 'Kyoto', 'Eiffel Tower', 'Rio de Janeiro').

    Returns:
        A concise summary string with facts and description of the queried destination.
    """
    try:
        title_encoded = urllib.parse.quote(location.strip().title().replace(" ", "_"))
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title_encoded}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "TravelConciergeAgent/1.0 (contact@example.com)",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("type") == "https://mediawiki.org/wiki/HyperSwitch/errors/not_found":
            return f"No Wikipedia summary found for location '{location}'."

        title = data.get("title", location)
        description = data.get("description", "")
        extract = data.get("extract", "No detailed summary available.")
        image_url = data.get("thumbnail", {}).get("source", "")

        result = f"Destination Overview: {title}"
        if description:
            result += f" ({description})"
        result += f"\n{extract}"
        if image_url:
            result += f"\nImage Preview: {image_url}"

        return result
    except Exception as e:
        return f"Error fetching Wikipedia summary for '{location}': {e}"


def convert_currency(amount: float, from_currency: str = "USD", to_currency: str = "EUR") -> str:
    """Converts a monetary amount between currencies using live exchange rates.

    Args:
        amount: The monetary amount to convert (e.g. 200.0).
        from_currency: 3-letter source currency code (e.g. 'USD').
        to_currency: 3-letter target currency code (e.g. 'JPY', 'EUR', 'GBP').

    Returns:
        A string summarizing the converted amount and current exchange rate.
    """
    try:
        from_code = from_currency.upper().strip()
        to_code = to_currency.upper().strip()
        url = f"https://open.er-api.com/v6/latest/{from_code}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("result") != "success":
            return f"Unable to fetch exchange rates for '{from_code}'."

        rates = data.get("rates", {})
        if to_code not in rates:
            return f"Currency code '{to_code}' is not supported."

        rate = rates[to_code]
        converted = amount * rate
        return (
            f"${amount:.2f} {from_code} = {converted:,.2f} {to_code} "
            f"(exchange rate: 1 {from_code} = {rate:.4f} {to_code})"
        )
    except Exception as e:
        return f"Error fetching live exchange rate: {e}"


def search_destinations(country: Optional[str] = None, max_budget: Optional[float] = None) -> str:
    """Searches travel destinations from the Firestore backend database.

    Args:
        country: Optional country name to filter destinations by (case-insensitive substring match).
        max_budget: Optional maximum average daily budget in USD.

    Returns:
        A summary string listing matching destination details.
    """
    try:
        query = firestore_db.collection("destinations")
        docs = query.stream()
        results = []

        for doc in docs:
            data = doc.to_dict()
            name = data.get("name", doc.id)
            doc_country = data.get("country", "")
            budget = data.get("avg_daily_budget_usd", data.get("budget_per_day", 0.0))
            category = data.get("category", "General")
            best_season = data.get("best_season", "Anytime")
            description = data.get("description", "")

            if country and country.lower() not in doc_country.lower():
                continue
            if max_budget is not None and max_budget > 0 and budget > max_budget:
                continue

            results.append(
                f"- {name}, {doc_country} [{category}]: Avg daily budget ${budget:.0f}, Best season: {best_season}. {description}"
            )

        if not results:
            return "No matching destinations found in the backend database."

        return "Matching destinations:\n" + "\n".join(results)
    except Exception as e:
        return f"Error reading destinations from Firestore: {e}"


def add_destination(
    name: str,
    country: str,
    avg_daily_budget_usd: float,
    category: str,
    best_season: str,
    description: str,
) -> str:
    """Adds a new travel destination to the Firestore backend database.

    Args:
        name: City or destination name (e.g., 'Barcelona').
        country: Country name (e.g., 'Spain').
        avg_daily_budget_usd: Estimated average daily cost in USD (e.g., 180.0).
        category: Trip category (e.g., 'Culture & Cuisine', 'Beach & Nature', 'Adventure').
        best_season: Best season to visit (e.g., 'Spring & Autumn').
        description: Short description of the destination.

    Returns:
        Confirmation string upon adding the destination to Firestore.
    """
    try:
        doc_id = name.lower().replace(" ", "-")
        doc_ref = firestore_db.collection("destinations").document(doc_id)
        doc_data = {
            "id": doc_id,
            "name": name,
            "country": country,
            "category": category,
            "best_season": best_season,
            "avg_daily_budget_usd": float(avg_daily_budget_usd),
            "description": description,
            "rating": 4.5,
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        doc_ref.set(doc_data)
        return f"Successfully saved new destination '{name}, {country}' to Firestore database."
    except Exception as e:
        return f"Error adding destination to Firestore: {e}"


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        query: The name of the city or timezone query.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


# Read agent engine resource name from deployment_metadata.json for AgentEngineSandboxCodeExecutor
metadata_path = Path(__file__).parent.parent / "deployment_metadata.json"
agent_engine_id = None
if metadata_path.exists():
    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata_content = json.load(f)
            agent_engine_id = metadata_content.get("remote_agent_runtime_id")
    except Exception:
        pass

sandbox_code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=agent_engine_id
)


async def generate_memories_callback(callback_context: CallbackContext):
    try:
        await callback_context.add_session_to_memory()
    except ValueError as e:
        if "memory service is not available" in str(e):
            pass
        else:
            raise
    return None


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are an expert Travel Concierge Agent. You help users plan trips by searching destination options, "
        "recommending locations based on budget or country, checking weather, fetching landmark & location facts, "
        "geocoding addresses, finding nearby places/attractions, generating destination postcard images, "
        "converting travel budgets to local currencies, adding new destinations to your database, "
        "executing Python code safely in a sandbox when calculations or data manipulation are required, "
        "and remembering all user preferences, facts, and user allergies or dietary restrictions across conversations. "
        "Always keep user allergies top of mind when recommending places, food, or travel itineraries."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property (\'h1\', \'h2\', \'body\') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or \'kind\'/\'data\'/\'metadata\' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=sandbox_code_executor,
    instruction=instruction,
    tools=[
        get_weather,
        get_current_time,
        search_destinations,
        add_destination,
        convert_currency,
        fetch_destination_summary,
        geocode_address,
        find_nearby_places,
        generate_destination_image,
        generate_destination_video,
        PreloadMemoryTool(),
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)






