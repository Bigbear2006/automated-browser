from abc import ABC, abstractmethod

from agents import FunctionTool
from playwright.async_api import Browser, BrowserContext, Page

from app.logging import logger


class BaseAgentTools(ABC):
    def __init__(self, browser: Browser, context: BrowserContext) -> None:
        self.browser = browser
        self.context = context

    async def get_active_page(self) -> Page:
        for page in self.context.pages:
            visible_state = await page.evaluate('document.visibilityState')
            if visible_state == 'visible':
                return page

        logger.warning(
            '[*] Opening browser page because there is no active page'
        )
        return await self.browser.new_page()

    @abstractmethod
    def get_all(self) -> list[FunctionTool]: ...
