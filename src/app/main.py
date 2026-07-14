import argparse
import asyncio

from agents import (
    Model,
    ModelProvider,
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
)
from openai import AsyncOpenAI

from src.app.config import config
from src.app.repl import BrowserREPL

client = AsyncOpenAI(base_url=config.BASE_URL, api_key=config.API_KEY)
set_tracing_disabled(disabled=True)


class CustomModelProvider(ModelProvider):
    def get_model(self, model_name: str | None) -> Model:
        return OpenAIChatCompletionsModel(
            model=model_name or config.MODEL_NAME, openai_client=client
        )


CUSTOM_MODEL_PROVIDER = CustomModelProvider()


async def main():
    parser = argparse.ArgumentParser(
        description='Browser automation with AI agent'
    )
    parser.add_argument(
        '--url',
        default='about:blank',
        help='Initial URL to navigate to (default: about:blank)',
    )
    parser.add_argument(
        '--headless', action='store_true', help='Run browser in headless mode'
    )
    args = parser.parse_args()

    repl = BrowserREPL(CUSTOM_MODEL_PROVIDER)
    await repl.run_interactive(initial_url=args.url, headless=args.headless)


if __name__ == '__main__':
    asyncio.run(main())
