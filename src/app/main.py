import argparse
import asyncio
import logging.config
import subprocess

from agents import SQLiteSession
from playwright.async_api import (
    async_playwright,
)

from app.agents import get_main_agent
from app.browser_manager import BrowserManager
from app.config import config
from app.logging import LOGGING
from app.model_provider import CUSTOM_MODEL_PROVIDER
from app.repl import BrowserREPL


async def main() -> None:
    logging.config.dictConfig(LOGGING)

    parser = argparse.ArgumentParser(
        description='Browser automation with AI agent'
    )
    parser.add_argument(
        '--url',
        default='chrome://newtab',
        help='Initial URL to navigate to (chrome://new-tab)',
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode (user can call tools)',
    )
    args = parser.parse_args()

    subprocess.Popen(
        [
            rf'{config.CHROME_PATH}',
            f'--remote-debugging-port={config.CHROME_PORT}',
            rf'--user-data-dir={config.USER_DATA_DIR}',
            '--no-first-run',
            '--no-default-browser-check',
        ]
    )

    playwright_instance = await async_playwright().start()
    browser = await playwright_instance.chromium.connect_over_cdp(
        f'http://127.0.0.1:{config.CHROME_PORT}',
    )

    browser_manager = await BrowserManager.create(browser)
    agent = get_main_agent(browser_manager)
    repl = BrowserREPL(
        agent,
        model_provider=CUSTOM_MODEL_PROVIDER,
        session=SQLiteSession('session', 'session.db'),
        max_turns=20,
    )

    try:
        await repl.run_interactive(initial_url=args.url)
    finally:
        await browser.close()
        await playwright_instance.stop()


if __name__ == '__main__':
    asyncio.run(main())
