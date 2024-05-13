import json
import os

STORAGE_OPTIONS = json.loads(os.environ.get("STORAGE_OPTIONS", "{}"))
STORAGE_PREFIX = os.environ.get("STORAGE_PREFIX", "memory://")

SAFETY_URL = os.environ.get("SAFETY_URL")

TOOLS_PATH = os.environ.get("TOOLS")
TOOLS = []
if TOOLS_PATH:
    with json.loads(TOOLS_PATH) as tool_file:
        TOOLS = tool_file
