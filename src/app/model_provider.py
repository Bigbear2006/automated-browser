from agents import (
    Model,
    ModelProvider,
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
)
from openai import AsyncOpenAI

from app.config import config

client = AsyncOpenAI(base_url=config.BASE_URL, api_key=config.API_KEY)
set_tracing_disabled(disabled=True)


class CustomModelProvider(ModelProvider):
    def get_model(self, model_name: str | None) -> Model:
        return OpenAIChatCompletionsModel(
            model=model_name or config.MODEL_NAME, openai_client=client
        )


CUSTOM_MODEL_PROVIDER = CustomModelProvider()
