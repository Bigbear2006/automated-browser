import argparse
import asyncio
import logging.config
import subprocess

from agents import (
    Model,
    ModelProvider,
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
)
from openai import AsyncOpenAI

from app.config import config
from app.logging import LOGGING
from app.repl import BrowserREPL

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
        default='chrome://newtab',
        help='Initial URL to navigate to (chrome://new-tab)',
    )
    parser.add_argument(
        '--headless', action='store_true', help='Run browser in headless mode'
    )
    args = parser.parse_args()

    subprocess.Popen(
        [
            rf'{config.CHROME_PATH}',
            '--remote-debugging-port=9222',
            rf'--user-data-dir={config.USER_DATA_DIR}',
            '--no-first-run',
            '--no-default-browser-check',
        ]
    )

    logging.config.dictConfig(LOGGING)

    repl = BrowserREPL(CUSTOM_MODEL_PROVIDER)
    await repl.run_interactive(initial_url=args.url, headless=args.headless)


if __name__ == '__main__':
    asyncio.run(main())
