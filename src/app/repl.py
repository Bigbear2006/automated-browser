import asyncio
import os
import sys

from app.logging import logger
from app.tools import (
    close_tab,
    create_tab,
    get_active_tab_index,
    get_all_tabs,
    get_page_elements,
    switch_to_tab,
)

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001')
    sys.stdout.reconfigure(encoding='utf-8')

from agents import Agent, RunConfig, Runner, SQLiteSession

from app.tools import (
    browser_service,
    click_element,
    get_current_url,
    get_page_snapshot,
    navigate_to,
    press_key_on_element,
    take_screenshot,
    type_into_element,
)

# ruff: disable[E501]
AGENT_INSTRUCTIONS = """
You are a browser automation assistant.
Your task is to help the user control a web browser by:
1. Use Extractor Agent to get page snapshots. Then analyze the page snapshot to understand the current state
2. Use Navigator Agent to navigate to URLs, and handle browser tabs
3. Using available tools interact with elements, and complete tasks
3. Reporting what you're doing and the results of your actions
4. Stop and ask user on destructive and important actions: (delete, send, etc)

Use the element references (like [ref=e1]) from snapshots to interact with elements.
Be helpful and explain your actions, answer shortly.
If you can't do what user's ask, tell about it, don't call tools endlessly
"""
# ruff: enable[e501]


class BrowserREPL:
    def __init__(self, model_provider):
        self.model_provider = model_provider
        self.extractor_agent = Agent(
            name='Extractor Agent',
            handoff_description=(
                'Agent for that extracts elements from HTML pages'
            ),
            instructions=(
                'You are assistant to help extract elements from HTML pages'
            ),
            tools=[get_page_elements, get_page_snapshot],
        )
        self.navigator_agent = Agent(
            name='Navigator Agent',
            handoff_description=(
                'You are agent that can handle navigation and browser tabs'
            ),
            tools=[
                navigate_to,
                create_tab,
                get_all_tabs,
                get_active_tab_index,
                switch_to_tab,
                close_tab,
            ],
        )
        self.agent = Agent(
            name='Browser Automation Agent',
            instructions=AGENT_INSTRUCTIONS,
            tools=[
                get_current_url,
                take_screenshot,
                click_element,
                type_into_element,
                press_key_on_element,
            ],
            handoffs=[self.extractor_agent, self.navigator_agent],
        )
        self.session = SQLiteSession('session', 'session.db')

    async def process_command(self, user_input: str) -> str:
        """Process user command through the agent."""
        try:
            logger.info('[*] Thinking...')
            result = await Runner.run(
                self.agent,
                user_input,
                session=self.session,
                run_config=RunConfig(model_provider=self.model_provider),
            )
            return result.final_output or 'Task completed.'
        except Exception as e:
            logger.error(f'{e.__class__.__name__}: {e}')
            return 'Task failed.'

    async def run_interactive(
        self, initial_url: str = 'about:blank', headless: bool = False
    ):
        """Run interactive REPL loop."""
        logger.info('[*] Browser Automation REPL')
        logger.info('=' * 50)
        logger.info(f'Starting browser with initial URL: {initial_url}')
        logger.info(
            "Type 'help' for commands, 'clear' to clear context, "
            "'exit' to quit"
        )
        logger.info('=' * 50)

        try:
            async with browser_service.managed_browser(
                headless=headless, url=initial_url
            ):
                logger.info('[+] Browser launched\n')

                while True:
                    try:
                        user_input = (
                            await asyncio.get_event_loop().run_in_executor(
                                None, input, '> '
                            )
                        )
                        user_input = user_input.strip().lower()

                        if not user_input:
                            continue

                        if user_input == 'exit':
                            logger.info('[*] Goodbye!')
                            break

                        elif user_input == 'clear':
                            await self.session.clear_session()
                            logger.info('\n[*] Current session cleared\n')

                        elif user_input == 'help':
                            print_help()
                            continue

                        elif user_input == 'snapshot':
                            snapshot = await get_page_snapshot()
                            logger.info(f'\n[*] Page Snapshot:\n{snapshot}\n')
                            continue

                        response = await self.process_command(user_input)
                        logger.info(f'{response}\n')

                    except KeyboardInterrupt:
                        logger.info('\n[!] Interrupted')
                        break
                    except Exception as e:
                        logger.info(f'[-] Error: {str(e)}')
                        raise e

        except Exception as e:
            logger.info(f'[-] Failed to launch browser: {str(e)}')


def print_help():
    logger.info(
        '\n[*] Available Commands:\n'
        '  snapshot          - Show current page snapshot\n'
        '  <command>         - Natural language command for the agent\n'
        '  exit              - Close browser and exit\n'
        '  clear             - Clear session context\n'
        '  help              - Show this help message\n\n'
        '[*] Examples:\n'
        '  Navigate to https://google.com\n'
        '  Click the search box and type hello\n'
        '  Find the button labeled Submit and click it\n'
        '  Fill the login form with username=john password=secret\n\n'
    )
