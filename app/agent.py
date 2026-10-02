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

import json
from pathlib import Path

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.a2ui_utils import a2ui_callback
from app.external_api import fetch_external_recipes
from app.firestore_db import (
    add_recipe,
    get_meal_plan,
    get_recipe_by_id,
    save_meal_plan,
    search_recipes,
)
from app.image_tool import generate_dish_image
from app.maps_tools import find_nearby_places, geocode_address
from app.video_tool import generate_cooking_video

# Load agent_engine_resource_name from deployment_metadata.json if available
_metadata_path = Path(__file__).resolve().parent.parent / "deployment_metadata.json"
_agent_engine_resource_name = None
_agent_engine_id = "7139277982975131648"
if _metadata_path.exists():
    try:
        with open(_metadata_path, "r") as _f:
            _meta = json.load(_f)
            _agent_engine_resource_name = _meta.get("remote_agent_runtime_id")
            if _agent_engine_resource_name:
                _agent_engine_id = _agent_engine_resource_name.split("/")[-1]
    except Exception:
        pass

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=_agent_engine_resource_name
)


async def generate_memories_callback(callback_context: CallbackContext):
    """Sends session events to Vertex AI Memory Bank for automatic allergy and preference extraction."""
    await callback_context.add_session_to_memory()
    return None


def memory_service_builder():
    """Configures Vertex AI Memory Bank service for deployment on Agent Runtime."""
    return VertexAiMemoryBankService(
        project="qwiklabs-gcp-02-82ea50e03721",
        location="us-central1",
        agent_engine_id=_agent_engine_id,
    )


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are a Personal Chef & Recipe Assistant. Help users find, prepare, "
        "and schedule recipes, locate supermarkets, perform recipe calculations via Python code execution, and generate visual dish photos."
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
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "MEMORY & ALLERGY SAFETY RULES: Remember all stated user allergies, intolerances, dietary restrictions, and preferences across sessions. "
        "ALWAYS cross-reference past user memories for allergies whenever recommending recipes or planning meals. "
        "NEVER suggest or include any ingredient the user is allergic to. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
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
    instruction=instruction,
    code_executor=code_executor,
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
    tools=[
        PreloadMemoryTool(),
        search_recipes,
        get_recipe_by_id,
        add_recipe,
        save_meal_plan,
        get_meal_plan,
        fetch_external_recipes,
        geocode_address,
        find_nearby_places,
        generate_dish_image,
        generate_cooking_video,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)



