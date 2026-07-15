import asyncio
import os
import sys
from asyncio import CancelledError

from app.logging import logger
from app.tools import (
    close_tab,
    create_tab,
    get_active_tab_index,
    get_all_tabs,
    switch_to_tab,
    wait,
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
    type_into_element,
)

# ruff: disable[E501]
AGENT_INSTRUCTIONS = """
You are a browser automation assistant.
Your task is to help the user control a web browser by:
1. Use Extractor Agent to get page snapshots. Then analyze the page snapshot to understand the current state.
Then you can use snapshot refs or element texts (e. g. Submit') to click elements
2. Use Navigator Agent to navigate to URLs, and handle browser tabs
3. Using available tools interact with elements, and complete tasks
4. Reporting what you're doing and the results of your actions

IMPORTANT:
1. if user ask you a long task, split it into small tasks and use tools to do them.
You have tools to navigate, click, press, type text and extract elements.
2. DON'T ask user confirmation on common tasks (click, type text, press, navigate)!
Ask confirmation only if user asks to DELETE something
3. PLASE DON'T ASK CONFIRMATION ON SIMPLE TASKS, I'M TIRED!!!
ASK CONFIRMATION ONLY IF USER ASKS TO DELETE SOMETHING!!!
OTHERWISE, JUST DO WHAT USER ASKS!!!

Use the element references (like [ref=e1]) from snapshots to interact with elements.
When you need a specific element by its visible text or label, delegate to the Extractor Agent's,
then use click_element / type_into_element / press_key_on_element with those refs.
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
                'You are assistant to help extract elements from HTML pages. '
                'Use get_page_snapshot for the full page structure, '
                # 'get_page_elements for inputs/buttons/text blocks, and '
                # 'search_elements to find specific elements by keyword and '
                'return ranked refs the main agent can interact with.\n'
                "DON'T use get_snapshot tool more than two times in a row!\n"
                "DON'T navigate again if website redirects you!\n"
            ),
            tools=[get_page_snapshot],
        )
        self.navigator_agent = Agent(
            name='Navigator Agent',
            handoff_description=(
                'You are agent that can handle navigation and browser tabs.\n'
                'ALWAYS open pages in current tab using navigate_to.\n'
                "Don't create new tabs unless user asks to.\n"
                "IMPORTANT: tabs indexes starts from 0!\n"
                "Always use first tab (index 0) is user doesn't ask you to use another tab\n"
                "If website redirects you, don't navigate again to the same URL!\n"
            ),
            tools=[
                navigate_to,
                get_current_url,
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
                # take_screenshot,
                click_element,
                type_into_element,
                press_key_on_element,
                wait,
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
                max_turns=20,
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
                            logger.info('[*] Current session cleared\n')
                            continue

                        elif user_input == 'help':
                            print_help()
                            continue

                        elif user_input == 'snapshot':
                            snapshot = await get_page_snapshot()
                            logger.info(f'\n[*] Page Snapshot:\n{snapshot}\n')
                            continue

                        response = await self.process_command(user_input)
                        logger.info(f'{response}\n')

                    except (KeyboardInterrupt, CancelledError):
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
        '  <command>         - Natural language command for the agent\n'
        '  snapshot          - Show current page snapshot\n'
        '  clear             - Clear session context\n'
        '  exit              - Close browser and exit\n'
        '  help              - Show this help message\n\n'
        '[*] Examples:\n'
        '  Navigate to https://google.com\n'
        '  Click the search box and type hello\n'
        '  Find the button labeled Submit and click it\n'
        '  Fill the login form with username=john password=secret\n\n'
    )
