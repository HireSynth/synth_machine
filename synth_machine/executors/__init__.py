import os

DEBUG = os.environ.get("DEBUG")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
VERTEX_REGION = os.environ.get("VERTEX_REGION", "us-central1")
