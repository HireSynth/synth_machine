from synth_machine.providers.base import BaseProvider
from synth_machine.providers.lorem import LoremProvider
import logging
from typing import Dict, Optional, Tuple
import os

class ProviderFactory:

    def __init__(self):
        super().__init__()
        self.providers = self.initialise_providers()

    def initialise_providers(self) -> Dict[str, BaseProvider]:

        providers: Dict[str, BaseProvider] = {"lorem": LoremProvider()}
        if "OPENAI_API_KEY" in os.environ.keys():
            try:
                from synth_machine.providers.openai import OpenAIProvider
    
                providers["openai"] = OpenAIProvider()
            except ModuleNotFoundError:
                raise ModuleNotFoundError("Please install synth_machine with extra 'openai'")
        if "ANTHROPIC_API_KEY" in os.environ.keys():    
            try:
                from synth_machine.providers.anthropic import AnthropicProvider

                providers["anthropic"] = AnthropicProvider()        
            except ModuleNotFoundError:
                raise ModuleNotFoundError("Please install synth_machine with extra 'anthropic'")
        if "TOGETHER_API_KEY" in os.environ.keys():
            try:
                from synth_machine.providers.togetherai import TogetherAIProvider

                providers["togetherai"] = TogetherAIProvider()
            except ModuleNotFoundError:
                raise ModuleNotFoundError(
                    "Please install synth_machine with extra 'togetherai'"
                )
        return providers


    def get_provider(self, name: str) -> Tuple[Optional[BaseProvider], Optional[str]]:
        if name in self.providers.keys():
            return self.providers[name], None
        else:
            error_message = f"Provider: {name} not found"
            logging.error(error_message)
            return None, error_message