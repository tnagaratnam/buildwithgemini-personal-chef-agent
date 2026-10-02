"""Image generation function tool for Personal Chef agent."""

import inspect
import time
from google import genai
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types

PROJECT_ID = "qwiklabs-gcp-02-82ea50e03721"
BUCKET_NAME = "personal-chef-recipes-qwiklabs-gcp-02-82ea50e03721"


async def generate_dish_image(prompt: str, tool_context: ToolContext = None) -> str:
    """Generates a photo or visual preview of a dish/recipe using gemini-3.1-flash-lite-image in the global region.

    Saves the generated image as an artifact in the Playground panel and uploads the image bytes
    directly to the public Cloud Storage bucket, returning the public HTTPS URL.

    Args:
        prompt: Detailed description of the dish photo to generate (e.g. 'A delicious plate of creamy garlic parmesan pasta garnished with parsley').
        tool_context: ADK ToolContext injected automatically by the runtime.

    Returns:
        A string containing the public HTTPS URL of the uploaded image.
    """
    try:
        # 1. Initialize GenAI client in global region
        genai_client = genai.Client(
            vertexai=True, project=PROJECT_ID, location="global"
        )

        # 2. Call gemini-3.1-flash-lite-image model
        response = genai_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            ),
        )

        image_bytes = None
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    image_bytes = part.inline_data.data
                    break

        if not image_bytes:
            return f"Failed to generate image for prompt '{prompt}': No image bytes returned."

        timestamp = int(time.time())
        safe_slug = "".join(c if c.isalnum() else "_" for c in prompt[:20].lower()).strip("_")
        filename = f"dish_{safe_slug}_{timestamp}.jpeg"

        # (1) Save image artifact so it shows up in Playground's Artifacts panel
        if tool_context:
            artifact_part = types.Part.from_bytes(
                data=image_bytes, mime_type="image/jpeg"
            )
            save_res = tool_context.save_artifact(filename=filename, artifact=artifact_part)
            if inspect.isawaitable(save_res):
                await save_res

        # (2) Upload image bytes directly to GCS bucket (without writing local file)
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type="image/jpeg")

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        return f"Successfully generated dish image. Public URL: {public_url}"
    except Exception as e:
        return f"Error generating dish image: {str(e)}"
