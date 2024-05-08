import logging
import os
from typing import AsyncGenerator, Optional

from src.executors.base import BaseExecutor
from src.synth_machine_configs import ModelConfig

import vertexai
from vertexai.preview.generative_models import GenerativeModel


"""
    Available models:
      - gemini-pro

    All models versions can be seen here:
    https://cloud.google.com/vertex-ai/docs/generative-ai/learn/model-versioning
"""

vertex_region = os.environ.get("VERTEX_REGION", "us-central1")


class VertexExecutor(BaseExecutor):
    @staticmethod
    def post_process(output: dict) -> dict:
        return output

    @staticmethod
    async def generate(  # type: ignore
        user_prompt: Optional[str],
        system_prompt: Optional[str],
        json_schema: Optional[dict],
        model_config: ModelConfig,
        user: Optional[str],
    ) -> AsyncGenerator[str, dict]:
        # Use Ldn if possible, otherwise use Iowa
        vertexai.init(location=vertex_region)

        model = GenerativeModel(model_config.model_name)
        model_response = model.generate_content_async(str(user_prompt))
        chunk = (await model_response).candidates[0]
        safety = {
            cat.category.name: cat.probability.name
            for cat in list(chunk.safety_ratings)
            if cat.probability.name != "NEGLIGIBLE"
        }
        text = chunk.text if len(safety) == 0 else ""
        logging.debug(
            {
                "token": chunk.text,
                "characters": len(chunk.text),
                "end": chunk.finish_reason.name,
                "flush": True,
            }
        )
        yield (text, {"safety": safety, "tokens": len(text)})  # type: ignore
