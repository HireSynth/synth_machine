from synth_machine.operator_setup import SynthConfig, ToolConfig


class BaseCost:
    async def record_tool_token_usage(
        self, user: str, session_id: str, tool_config: ToolConfig, num_tokens: float
    ) -> float:
        return num_tokens

    async def record_prompt_token_usage(
        self,
        user: str,
        session_id: str,
        synth_config: SynthConfig,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> int:
        return input_tokens + output_tokens

    async def calculate_chunk_cost(
        self,
        stage: str,
        synth_config: SynthConfig,
        num_tokens: int,
    ) -> int:
        return num_tokens
