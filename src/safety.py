import logging
from enum import Enum
from typing import Optional, TypedDict

from openai import OpenAI, RateLimitError
from opa_client.opa import OpaClient
from urllib3.exceptions import LocationValueError, MaxRetryError
from core.settings import SAFETY_URL

opa_client = OpaClient(host=SAFETY_URL, port=8181)


class Threshold(Enum):
    high = "high"
    moderate = "moderate"
    low = "low"
    negligible = "negligible"


class SafetyThresholds(TypedDict):
    score: Threshold
    flagged: bool


class SafetyInput(TypedDict):
    hate: Threshold
    harassment: Threshold
    sexual_content: Threshold
    dangerous: Threshold


class SafetyResponse(TypedDict):
    hate: SafetyThresholds
    harassment: SafetyThresholds
    sexual_content: SafetyThresholds
    dangerous: SafetyThresholds


SAFETY_DEFAULTS: SafetyInput = {
    "hate": Threshold.moderate,
    "harassment": Threshold.moderate,
    "sexual_content": Threshold.moderate,
    "dangerous": Threshold.moderate,
}

default_response = {
    "hate": {"score": "negligible", "flagged": False},
    "harassment": {"score": "negligible", "flagged": False},
    "sexual_content": {
        "score": "negligible",
        "flagged": False,
    },
    "dangerous": {"score": "negligible", "flagged": False},
}


class Safety:
    def __init__(
        self, user_thresholds: Optional[SafetyInput], synth_thresholds: SafetyInput
    ):
        self.synth_thresholds = synth_thresholds
        self.user_thresholds = user_thresholds if user_thresholds else synth_thresholds

    def check(
        self,
        text: str,
        provider: str,
    ) -> dict:
        match provider:
            case "openai":
                try:
                    response = OpenAI().moderations.create(input=text)
                except RateLimitError:
                    logging.error("Safety provider rate limited")
                    return default_response
                scores = dict(response.results[0].category_scores)
            case _:
                logging.error("No safety provider specified")
                return default_response

        # Call policy server
        try:
            safety_result = opa_client.check_permission(
                input_data={
                    "input": {
                        "message": {
                            "moderation_scores": scores,  # type: ignore
                        },
                        "user_thresholds": self.user_thresholds,
                        "synth_thresholds": self.synth_thresholds,
                    }
                },
                policy_name="policies/policy.rego",
                rule_name="result",
            ).get("result")
        except (LocationValueError, MaxRetryError):
            logging.error("Safety policy server not reachable")
            return default_response
        return safety_result

    def flagged(self, safety_response: dict) -> bool:
        return (
            len(
                [
                    safety_response[key]["flagged"]
                    for key in safety_response.keys()
                    if safety_response[key]["flagged"]
                ]
            )
            != 0
        )
