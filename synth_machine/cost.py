from synth_machine.config import SynthConfig


class BaseCost:
    async def calculate_tool_token_usage(self, config: dict, num_tokens: int) -> int:
        return num_tokens

    async def calculate_prompt_token_usage(
        self, llm_id, input_tokens: int = 0, output_tokens: int = 0
    ) -> int:
        return input_tokens + output_tokens

    def calculate_chunk_cost(self, config: SynthConfig, num_tokens: int) -> int:
        return num_tokens
