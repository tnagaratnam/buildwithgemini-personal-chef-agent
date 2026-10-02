"""Custom service registry for personal-chef-agent."""

from google.adk.cli.service_registry import get_service_registry
from google.adk.memory import VertexAiMemoryBankService


def agentengine_memory_factory(uri: str, **kwargs):
    """Factory to instantiate VertexAiMemoryBankService for agentengine:// URIs."""
    # Extract ID from agentengine://<ID>
    agent_engine_id = uri.replace("agentengine://", "").strip("/")
    return VertexAiMemoryBankService(
        project="qwiklabs-gcp-02-82ea50e03721",
        location="us-central1",
        agent_engine_id=agent_engine_id,
    )


get_service_registry().register_memory_service("agentengine", agentengine_memory_factory)
