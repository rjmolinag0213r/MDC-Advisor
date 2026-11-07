"""Tests run fully offline: no LLM or Swarms calls, whatever is in backend/.env."""
import os
import sys
from pathlib import Path

# must be set before app/llm/roadmap import (load_dotenv never overrides existing vars)
import tempfile

os.environ["LLM_PROVIDERS"] = "none"
os.environ["SWARMS_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""
os.environ["DATABASE_URL"] = ""
os.environ["AUTH0_DOMAIN"] = ""
os.environ["AUTH0_AUDIENCE"] = ""
os.environ["RATE_LIMIT_PER_MIN"] = "1000"
os.environ["SQLITE_PATH"] = os.path.join(tempfile.mkdtemp(prefix="nextstop-test-"), "test.db")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402


@pytest.fixture()
def client():
    import app as app_module
    import roadmap
    roadmap.CACHE.clear()
    app_module._hits.clear()
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c
