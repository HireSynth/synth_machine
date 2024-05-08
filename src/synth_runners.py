import os
import logging
from io import BytesIO
from typing import Optional
from uuid import uuid4

import jq
import requests  # type: ignore

from apps.synth_api.models.blob import Blob

GS_BUCKET_PREFIX = os.environ.get("GS_BUCKET_PREFIX", "")


async def tool_runner(config: dict, return_key: Optional[str]) -> Optional[dict | str]:
    response = requests.post(
        config["tool_path"],
        json=config["payload"],
    )

    if config["output_mime_types"]:
        output_format = response.headers["content-type"].split("/")[1]
        file_name = f"{uuid4()}.{output_format}"

        blob = await Blob.create_blob(
            file_name,
            config["id"],
            config["owner"],
            BytesIO(response.content),
        )
        return {
            "__blob": blob.id,  # type: ignore
            "file_name": file_name,
            "mime_type": output_format,
            "url": blob.file.storage.url(blob.file.name)
            if GS_BUCKET_PREFIX == "local"
            else blob.file.name,
        }
    else:
        output = response.json()
        return output if not return_key else output[return_key]


def jq_runner(jq_command: str, data: dict = {}, schema: dict = {}) -> list:
    if not jq_command:
        return []
    try:
        intermediate_result = jq.compile(jq_command).input_value(data)
        if schema.get("type") == "object" or schema.get("type") == "string":
            return intermediate_result.first()
        else:
            return intermediate_result.all()
    except Exception as e:
        logging.warn(f"Error in post processing task {e}")
        return []
