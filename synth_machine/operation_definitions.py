try:
    from enum import StrEnum
except ImportError:
    # For python versions <3.11, using aenum for backward compatibility
    from aenum import StrEnum


class YieldTasks(StrEnum):  # type: ignore
    CHUNK = "CHUNK"
    MODEL_CONFIG = "MODEL_CONFIG"
    SET_MEMORY = "SET_MEMORY"
    SET_ACTIVE_OUTPUT = "SET_ACTIVE_OUTPUT"


class FailureState(StrEnum):  # type: ignore
    FAILED = "FAILED"
    LOOP_FAILURE = "LOOP_FAILED"
    OUTPUT_VALIDATION_FAILED = "OUTPUT_VALIDATION_FAILED"
    NOT_IMPLEMENTED = "NOT IMPLEMENTED"


class PostProcessTasks(StrEnum):  # type: ignore
    JQ = "jq"


class OperationPriority(StrEnum):  # type: ignore
    APPEND = "append"
    INTERLEAVE = "interleave"
    JINJA = "jinja"
    PROMPT = "prompt"
    RESET = "reset"
    UDF = "udf"
    TOOL = "tool"
    RAG = "rag"
