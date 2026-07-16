from agents import FunctionTool, function_tool
from playwright.async_api import Locator

from app.tools.base import BaseAgentTools


class InteractorAgentTools(BaseAgentTools):
    def get_all(self) -> list[FunctionTool]:
        return [
            function_tool(func)
            for func in (
                self.click,
                self.type_text,
                self.press_key,
                self.screenshot,
                self.wait,
            )
        ]

    async def find_element(self, ref: str) -> Locator:
        page = await self.get_active_page()

        # Try using locator with aria attributes first
        locator = page.locator(f'aria-ref={ref}')
        count = await locator.count()

        if count == 0:
            # Then our custom ref
            locator = page.locator(f'[data-agent-ref={ref}]')
            count = await locator.count()

        if count == 0:
            locator = page.get_by_text(ref)

        return locator

    async def click(self, ref: str) -> str:
        """
        Click an element by its reference.
        Reference can be:
        - 'e1', 'e2' ref from the snapshot;
        - element text from the snapshot;
        """

        locator = await self.find_element(ref)
        count = await locator.count()

        if count > 0:
            await locator.first.click()
            return f'Clicked element {ref}'

        return f'Element {ref} not found'

    async def type_text(self, ref: str, text: str) -> str:
        """Type text into an element by its reference."""

        locator = await self.find_element(ref)
        count = await locator.count()

        if count > 0:
            await locator.first.fill(text)
            return f'Typed text into element {ref}'

        return (
            f'Could not type into element {ref}. More likely element not found'
        )

    async def press_key(self, ref: str, key: str) -> str:
        """Press a keyboard key on an element.

        Args:
            ref: Element reference from the snapshot
            key: Key name (e.g., 'Enter', 'Tab', 'Escape', 'ArrowDown')

        Returns: message"""

        locator = await self.find_element(ref)
        count = await locator.count()

        if count > 0:
            await locator.first.press(key)
            return f'Pressed key {key} on element ref'

        return f'Could not press key {key} on element {ref}'

    async def screenshot(self) -> bytes:
        """Take page screenshot"""
        page = await self.get_active_page()
        return await page.screenshot()

    async def wait(self, timeout: int) -> str:
        """Wait for given number of milliseconds.
        Use this ONLY IF page isn't loaded yet"""
        page = await self.get_active_page()
        await page.wait_for_timeout(timeout)
        return f'Wait for {timeout} milliseconds...'
