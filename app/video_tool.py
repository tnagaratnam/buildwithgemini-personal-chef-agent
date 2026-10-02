"""Video generation function tool for Personal Chef agent using gemini-omni-flash-preview."""

import base64
import inspect
import time
import google.auth
import google.auth.transport.requests
import requests
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types

PROJECT_ID = "qwiklabs-gcp-02-82ea50e03721"
BUCKET_NAME = "personal-chef-recipes-qwiklabs-gcp-02-82ea50e03721"


async def generate_cooking_video(prompt: str, tool_context: ToolContext = None) -> str:
    """Generates a short video clip of dish preparation or cooking technique using gemini-omni-flash-preview in global region.

    Saves the generated video as an artifact in the Playground panel and uploads the video bytes
    directly to the public Cloud Storage bucket, returning the public HTTPS URL.

    Args:
        prompt: Detailed description of the cooking technique or dish video to generate (e.g. 'A short video of a chef tossing fresh pasta in garlic butter sauce').
        tool_context: ADK ToolContext injected automatically by the runtime.

    Returns:
        A string containing the public HTTPS URL of the uploaded video.
    """
    try:
        # 1. Fetch default GCP credentials for Vertex AI Interactions API
        credentials, project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)
        token = credentials.token

        # 2. Call Interactions API in global region with model gemini-omni-flash-preview
        url = f"https://aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/global/interactions"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        body = {
            "model": "gemini-omni-flash-preview",
            "input": [
                {
                    "type": "text",
                    "text": prompt,
                }
            ],
        }

        resp = requests.post(url, headers=headers, json=body, timeout=120)
        if resp.status_code != 200:
            return f"Error from Interactions API (HTTP {resp.status_code}): {resp.text}"

        data = resp.json()
        video_bytes = None

        if "steps" in data:
            for step in data["steps"]:
                for c in step.get("content", []):
                    if c.get("type") == "video" or c.get("mime_type") == "video/mp4":
                        if "data" in c and c["data"]:
                            video_bytes = base64.b64decode(c["data"])
                            break
                        elif "uri" in c and c["uri"]:
                            video_resp = requests.get(c["uri"], timeout=60)
                            if video_resp.status_code == 200:
                                video_bytes = video_resp.content
                            break

        if not video_bytes:
            return f"Failed to generate video for prompt '{prompt}': No video bytes returned in response."

        timestamp = int(time.time())
        safe_slug = "".join(c if c.isalnum() else "_" for c in prompt[:20].lower()).strip("_")
        filename = f"video_{safe_slug}_{timestamp}.mp4"

        # (1) Save video artifact so it shows up in Playground's Artifacts panel
        if tool_context:
            artifact_part = types.Part.from_bytes(
                data=video_bytes, mime_type="video/mp4"
            )
            save_res = tool_context.save_artifact(filename=filename, artifact=artifact_part)
            if inspect.isawaitable(save_res):
                await save_res

        # (2) Upload video bytes directly to public GCS bucket (without writing local file)
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type="video/mp4")

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        return f"Successfully generated cooking video. Public URL: {public_url}"
    except Exception as e:
        return f"Error generating cooking video: {str(e)}"
