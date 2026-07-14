import asyncio
import os
import sys

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001')
    sys.stdout.reconfigure(encoding='utf-8')

from agents import Agent, RunConfig

from src.app.tools import (
    browser_service,
    click_element,
    get_current_url,
    get_page_snapshot,
    navigate_to,
    press_key_on_element,
    take_screenshot,
    type_into_element,
)


class BrowserREPL:
    def __init__(self, model_provider):
        self.model_provider = model_provider
        self.agent = Agent(
            name='Browser Automation Agent',
            instructions="""You are a browser automation assistant. Your task is to help the user control a web browser by:
1. Analyzing the page snapshot to understand the current state
2. Using available tools to navigate, interact with elements, and complete tasks
3. Reporting what you're doing and the results of your actions

Always start by getting the page snapshot to see what you're working with.
Use the element references (like [ref=e1]) from snapshots to interact with elements.
Be helpful and explain your actions.""",
            tools=[
                get_page_snapshot,
                navigate_to,
                click_element,
                type_into_element,
                press_key_on_element,
                get_current_url,
                take_screenshot,
            ],
        )

    async def process_command(self, user_input: str) -> str:
        """Process user command through the agent."""
        from agents import Runner

        try:
            print('[*] Thinking...')
            result = await Runner.run(
                self.agent,
                user_input,
                run_config=RunConfig(model_provider=self.model_provider),
            )
            return result.final_output or 'Task completed.'
        except Exception as e:
            return f'Error: {str(e)}'

    async def run_interactive(
        self, initial_url: str = 'about:blank', headless: bool = False
    ):
        """Run interactive REPL loop."""
        print('[*] Browser Automation REPL')
        print('=' * 50)
        print(f'Starting browser with initial URL: {initial_url}')
        print("Type 'help' for commands, 'exit' to quit")
        print('=' * 50)

        try:
            async with browser_service.managed_browser(
                headless=headless, url=initial_url
            ):
                print('[+] Browser launched')
                print()

                while True:
                    try:
                        # Read user input
                        user_input = (
                            await asyncio.get_event_loop().run_in_executor(
                                None, sys.stdin.readline
                            )
                        )
                        user_input = user_input.strip()

                        if not user_input:
                            continue

                        if user_input.lower() == 'exit':
                            print('[*] Goodbye!')
                            break

                        if user_input.lower() == 'help':
                            self._print_help()
                            continue

                        if user_input.lower() == 'snapshot':
                            snapshot = await get_page_snapshot()
                            print('\n[*] Page Snapshot:')
                            print(snapshot)
                            print()
                            continue

                        # Process command through agent
                        print(f'\n[*] Processing: {user_input}')
                        print('-' * 50)

                        response = await self.process_command(user_input)
                        print(response)
                        print()

                    except KeyboardInterrupt:
                        print('\n[!] Interrupted')
                        break
                    except Exception as e:
                        print(f'[-] Error: {str(e)}')
                        print()

        except Exception as e:
            print(f'[-] Failed to launch browser: {str(e)}')

    @staticmethod
    def _print_help():
        print('\n[*] Available Commands:')
        print('  snapshot          - Show current page snapshot')
        print('  <command>         - Natural language command for the agent')
        print('  exit              - Close browser and exit')
        print('  help              - Show this help message')
        print()
        print('[*] Examples:')
        print('  Navigate to https://example.com')
        print('  Click the search box and type hello')
        print('  Find the button labeled Submit and click it')
        print('  Fill the login form with username=john password=secret')
        print()
