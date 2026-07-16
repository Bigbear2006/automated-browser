from playwright.async_api import Browser, BrowserContext, Page

from app.logging import logger


class BrowserManager:
    def __init__(self, browser: Browser) -> None:
        self.browser = browser
        self._active_page_index = 0

    @classmethod
    async def create(cls, browser: Browser) -> 'BrowserManager':
        if not browser.contexts:
            await browser.new_context()
            logger.info('[*] Created a new context')

        if not browser.contexts[0].pages:
            await browser.contexts[0].new_page()
            logger.info('[*] Opened a new page')

        return cls(browser)

    @property
    def context(self) -> BrowserContext:
        return self.browser.contexts[0]

    async def get_active_page(self) -> Page:
        return self.context.pages[self._active_page_index]

    def set_active_page(self, index: int) -> None:
        self._active_page_index = index
