import logging
from io import BytesIO
from typing import Optional
from uuid import uuid4

import jq
import requests  # type: ignore
from object_store import ObjectStore
import json
import os


STORAGE_OPTIONS = json.loads(os.environ.get("STORAGE_OPTIONS", "{}"))
STORAGE_PREFIX = os.environ.get("STORAGE_PREFIX", "memory://")


async def tool_runner(store: ObjectStore, config: dict) -> Optional[dict | str]:
    try:
        response = requests.post(
            config["tool_path"],
            json=config["payload"],
        )
        response_headers = {
            "response_headers": {
                "status": response.status_code,
                "success": response.ok,
            }
        }
    except Exception as e:
        logging.error(f"Error in running tool {e}")
        return

    if config["output_mime_types"]:
        output_format = response.headers["content-type"].split("/")[1]
        file_name = f"{uuid4()}.{output_format}"
        store.put(file_name, BytesIO(response.content))
        return {
            "file_name": file_name,
            "mime_type": output_format,
            "url": f"{STORAGE_PREFIX}/{file_name}",
            "response_headers": response_headers["response_headers"],
        }
    else:
        output = response.json() | response_headers
        return output


def jq_runner(jq_command: str, data: dict = {}, schema: Optional[dict] = {}) -> list:
    if not jq_command:
        return []
    try:
        intermediate_result = jq.compile(jq_command).input_value(data)
        if schema and (
            schema.get("type") == "object" or schema.get("type") == "string"
        ):
            return intermediate_result.first()
        else:
            return intermediate_result.all()
    except Exception as e:
        logging.warn(f"Error in post processing task {e}")
        return []
