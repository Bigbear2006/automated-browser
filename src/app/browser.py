import difflib
from contextlib import asynccontextmanager

from playwright.async_api import (
    Browser,
    BrowserContext,
    Locator,
    Page,
    async_playwright,
)

from app.logging import logger


@asynccontextmanager
async def managed_browser_context(
    browser_service, headless: bool = False, url: str = 'about:blank'
):
    """Context manager for browser lifecycle."""
    await browser_service.launch(headless=headless, url=url)
    try:
        yield browser_service
    finally:
        await browser_service.close()


class BrowserService:
    def __init__(self):
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.playwright_instance = None

    async def launch(self, headless: bool = False, url: str = 'about:blank'):
        """Launch browser and navigate to URL."""
        self.playwright_instance = await async_playwright().start()
        self.browser = (
            await self.playwright_instance.chromium.connect_over_cdp(
                'http://127.0.0.1:9222'
            )
        )

        if self.browser.contexts:
            self.context = self.browser.contexts[0]
        else:
            self.context = await self.browser.new_context()

        if self.context.pages:
            page = self.context.pages[0]
        else:
            logger.info('[+] Opening a new page')
            page = await self.context.new_page()

        await page.goto(url)

    async def close(self):
        page = await self.get_active_page()
        await page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright_instance:
            await self.playwright_instance.stop()

    async def get_snapshot(self, depth: int | None = None) -> str:
        """Get accessibility snapshot with element references for AI."""
        logger.info('[*] Get page snapshot')
        page = await self.get_active_page()
        snapshot = await page.locator('body').aria_snapshot(
            mode='ai', depth=depth
        )
        return snapshot

    async def navigate(self, url: str) -> str | None:
        logger.info(f'[*] Navigate to {url}')
        page = await self.get_active_page()
        rsp = await page.goto(url)
        return rsp.url if rsp else None

    async def find_element(self, ref: str) -> Locator:
        page = await self.get_active_page()

        # Try using locator with aria attributes first
        locator = page.locator(f'aria-ref={ref}')
        count = await locator.count()

        if count == 0:
            # Then our custom ref
            locator = page.locator(f'data-agent-ref={ref}')
            count = await locator.count()

        if count == 0:
            locator = page.get_by_text(ref)

        return locator

    async def click(self, ref: str) -> str:
        locator = await self.find_element(ref)
        count = await locator.count()

        if count > 0:
            await locator.first.click()
            return f'Clicked element {ref}'

        return f'Element {ref} not found'

    async def type_text(self, ref: str, text: str) -> str:
        locator = await self.find_element(ref)
        count = await locator.count()

        if count > 0:
            await locator.first.fill(text)
            return f'Typed text into element {ref}'

        return (
            f'Could not type into element {ref}. More likely element not found'
        )

    async def press_key(self, ref: str, key: str) -> str:
        locator = await self.find_element(ref)
        count = await locator.count()

        if count > 0:
            await locator.first.press(key)
            return f'Pressed key {key} on element ref'

        return f'Could not press key {key} on element {ref}'

    async def get_current_url(self) -> str:
        page = await self.get_active_page()
        logger.info(f'[*] Get current URL: {page.url}')
        return page.url

    async def wait(self, timeout: int) -> str:
        page = await self.get_active_page()
        await page.wait_for_timeout(timeout)
        return f'Wait for {timeout} milliseconds...'

    async def screenshot(self, path: str = 'screenshot.png') -> bytes:
        page = await self.get_active_page()
        return await page.screenshot(path=path)

    async def create_tab(self, url: str = 'about:blank') -> str:
        logger.info(f'[*] Create tab {url}')
        page = await self.context.new_page()
        if url != 'about:blank':
            await page.goto(url)
        return f'Новая вкладка успешно создана. Текущий URL: {page.url}'

    async def get_all_tabs(self) -> str:
        logger.info('[*] Get all tabs')
        pages = self.context.pages
        if not pages:
            return 'Нет открытых вкладок.'

        result = []
        for index, page in enumerate(pages):
            result.append(
                f'Индекс: {index} | URL: {page.url} | Заголовок: {await page.title()}'
            )
        return '\n'.join(result)

    async def get_active_page(self) -> Page:
        for page in self.context.pages:
            visible_state = await page.evaluate('document.visibilityState')
            if visible_state == 'visible':
                return page
        logger.warning(
            '[*] Opening browser page because there is no active page'
        )
        return await self.browser.new_page()

    async def get_active_page_index(self) -> int:
        logger.info('[*] Get active page index')
        page = await self.get_active_page()
        return self.context.pages.index(page)

    async def switch_to_tab(self, index: int) -> str:
        """Переключается на вкладку по её индексу (начиная с 0)."""
        logger.info(f'[*] Switch to tab {index}')
        pages = self.context.pages
        if index < 0 or index >= len(pages):
            return f'Ошибка: Вкладка с индексом {index} не найдена. Всего вкладок: {len(pages)}'

        await pages[index].bring_to_front()
        return f'Успешно переключено на вкладку {index}: {pages[index].url}'

    async def close_tab(self, index: int) -> str:
        """Закрывает вкладку по её индексу."""
        logger.info(f'[*] Close tab {index}')
        pages = self.context.pages
        if index < 0 or index >= len(pages):
            return f'Ошибка: Невозможно закрыть. Вкладка с индексом {index} не существует.'

        url_closed = pages[index].url
        await pages[index].close()
        return f'Вкладка с индексом {index} ({url_closed}) успешно закрыта.'

    def managed_browser(
        self, headless: bool = False, url: str = 'about:blank'
    ):
        """Return context manager for browser lifecycle."""
        return managed_browser_context(self, headless=headless, url=url)
