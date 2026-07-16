import asyncio

from agents import (
    Agent,
    ModelProvider,
    RunConfig,
    Runner,
    SessionABC,
)

from app.logging import logger


class BrowserREPL:
    def __init__(
        self,
        agent: Agent,
        *,
        model_provider: ModelProvider,
        session: SessionABC,
        max_turns: int,
    ):
        self.agent = agent
        self.model_provider = model_provider
        self.session = session
        self.max_turns = max_turns

    async def process_command(self, user_input: str) -> str:
        try:
            logger.info('[*] Thinking...')
            result = await Runner.run(
                self.agent,
                user_input,
                session=self.session,
                run_config=RunConfig(model_provider=self.model_provider),
                max_turns=self.max_turns,
            )
            return result.final_output or 'Task completed.'
        except Exception as e:
            logger.error(f'{e.__class__.__name__}: {e}')
            return 'Task failed.'

    async def run_interactive(self, initial_url: str = 'about:blank') -> None:
        logger.info('[*] Browser Automation REPL')
        logger.info('=' * 50)
        logger.info(f'Starting browser with initial URL: {initial_url}')
        logger.info(
            'Type /help for commands, /clear to clear context, /exit to quit'
        )
        logger.info('=' * 50)

        while True:
            try:
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, input, '> '
                )
                user_input = user_input.strip().lower()

                if not user_input:
                    continue

                if user_input == '/exit':
                    logger.info('[*] Goodbye!')
                    break

                elif user_input == '/clear':
                    await self.session.clear_session()
                    logger.info('[*] Current session cleared\n')
                    continue

                elif user_input == '/help':
                    print_help()
                    continue

                response = await self.process_command(user_input)
                logger.info(f'{response}\n')

            except (KeyboardInterrupt, asyncio.CancelledError):
                logger.info('[!] Interrupted\n')
                break

            except Exception as e:
                logger.info(f'[!] Error: {e}\n')
                raise e


def print_help() -> None:
    logger.info(
        '\n[*] Available Commands:\n'
        '  <command>         - Natural language command for the agent\n'
        '  /clear             - Clear session context\n'
        '  /exit              - Close browser and exit\n'
        '  /help              - Show this help message\n\n'
        '[*] Commands examples:\n'
        '  Navigate to https://google.com\n'
        '  Click the search box and type hello\n'
        '  Find the button labeled Submit and click it\n'
        '  Fill the login form with username=john password=secret\n\n'
    )
