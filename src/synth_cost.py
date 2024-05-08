class BaseCost:
    async def calculate_tool_token_usage(self, tool_id, token_cost) -> int:
        return 0

    async def calculate_prompt_token_usage(
        self, llm_id, input_tokens: int = 0, output_tokens: int = 0
    ) -> None:
        pass
