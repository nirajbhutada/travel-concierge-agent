import os
import pytest

@pytest.fixture(autouse=True, scope="session")
def setup_env():
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
    if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
        os.environ["GOOGLE_CLOUD_PROJECT"] = "qwiklabs-gcp-01-1a01cf2a0844"
