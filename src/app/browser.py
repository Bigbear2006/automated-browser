from contextlib import asynccontextmanager

from playwright.async_api import Browser, Page, async_playwright


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
        self.page: Page | None = None
        self.playwright_instance = None

    async def launch(self, headless: bool = False, url: str = 'about:blank'):
        """Launch browser and navigate to URL."""
        self.playwright_instance = await async_playwright().start()
        self.browser = await self.playwright_instance.chromium.launch(
            headless=headless
        )
        self.page = await self.browser.new_page()
        await self.page.goto(url)

    async def close(self):
        """Close browser."""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright_instance:
            await self.playwright_instance.stop()

    async def get_snapshot(self, depth: int = 3) -> str:
        """Get accessibility snapshot with element references for AI."""
        if not self.page:
            raise RuntimeError('Browser not initialized')

        snapshot = await self.page.locator('body').aria_snapshot(
            mode='ai', depth=depth
        )
        return snapshot

    async def navigate(self, url: str) -> str:
        """Navigate to URL."""
        if not self.page:
            raise RuntimeError('Browser not initialized')

        await self.page.goto(url)
        return await self.get_snapshot()

    async def _find_element_by_ref(self, ref: str):
        """Find an element using its aria-snapshot ref (e.g., e1, e2, etc)."""
        if not self.page:
            raise RuntimeError('Browser not initialized')

        # Playwright stores refs as attributes we can query
        # The ref format from aria_snapshot is [ref=eX]
        element = await self.page.query_selector(
            f"[data-aria-ref='{ref}'], [aria-ref='{ref}']"
        )

        if element:
            return element

        # Fallback: use JavaScript to find element by searching all elements
        # This is less efficient but works as a backup
        result = await self.page.evaluate(f"""
            (() => {{
                const ref = '{ref}';
                const elements = document.querySelectorAll('[data-aria-ref], [aria-ref]');
                for (let elem of elements) {{
                    if (elem.getAttribute('data-aria-ref') === ref || elem.getAttribute('aria-ref') === ref) {{
                        return elem;
                    }}
                }}
                // If still not found, try to extract index and use heuristics
                const idx = parseInt(ref.substring(1));
                const allInteractive = [
                    ...document.querySelectorAll('button, a[href], input, textarea, select, [role="button"], [role="link"]')
                ];
                return allInteractive[idx] || null;
            }})()
        """)

        return result

    async def click(self, ref: str) -> str:
        """Click element by ref."""
        if not self.page:
            raise RuntimeError('Browser not initialized')

        try:
            # Try using locator with aria attributes first
            locator = self.page.locator(
                f"[data-aria-ref='{ref}'], [aria-ref='{ref}']"
            )
            count = await locator.count()

            if count > 0:
                await locator.first.click()
            else:
                # Fallback: extract index and click from interactive elements
                ref_num = int(ref[1:]) if ref.startswith('e') else 0
                elements = await self.page.query_selector_all(
                    "button, a[href], input[type='button'], input[type='submit'], textarea, select, [role='button'], [role='link']"
                )
                if ref_num < len(elements):
                    await elements[ref_num].click()
                else:
                    raise ValueError(f'Element {ref} not found')
        except Exception as e:
            raise ValueError(f'Could not click element {ref}: {str(e)}')

        return await self.get_snapshot()

    async def type_text(self, ref: str, text: str) -> str:
        """Type text into element by ref."""
        if not self.page:
            raise RuntimeError('Browser not initialized')

        try:
            # Try aria attributes first
            locator = self.page.locator(
                f"[data-aria-ref='{ref}'], [aria-ref='{ref}']"
            )
            count = await locator.count()

            if count > 0:
                await locator.first.fill(text)
            else:
                # Fallback: use index approach
                ref_num = int(ref[1:]) if ref.startswith('e') else 0
                inputs = await self.page.query_selector_all('input, textarea')
                if ref_num < len(inputs):
                    await inputs[ref_num].fill(text)
                else:
                    raise ValueError(f'Input element {ref} not found')
        except Exception as e:
            raise ValueError(f'Could not type into element {ref}: {str(e)}')

        return await self.get_snapshot()

    async def press_key(self, ref: str, key: str) -> str:
        """Press key on element by ref."""
        if not self.page:
            raise RuntimeError('Browser not initialized')

        try:
            locator = self.page.locator(
                f"[data-aria-ref='{ref}'], [aria-ref='{ref}']"
            )
            count = await locator.count()

            if count > 0:
                await locator.first.press(key)
            else:
                ref_num = int(ref[1:]) if ref.startswith('e') else 0
                elements = await self.page.query_selector_all(
                    "input, textarea, button, a, [role='button']"
                )
                if ref_num < len(elements):
                    await elements[ref_num].press(key)
                else:
                    raise ValueError(f'Element {ref} not found')
        except Exception as e:
            raise ValueError(f'Could not press key on element {ref}: {str(e)}')

        return await self.get_snapshot()

    async def get_current_url(self) -> str:
        """Get current URL."""
        if not self.page:
            raise RuntimeError('Browser not initialized')
        return self.page.url

    async def screenshot(self, path: str = 'screenshot.png') -> str:
        """Take screenshot."""
        if not self.page:
            raise RuntimeError('Browser not initialized')

        await self.page.screenshot(path=path)
        return f'Screenshot saved to {path}'

    def managed_browser(
        self, headless: bool = False, url: str = 'about:blank'
    ):
        """Return context manager for browser lifecycle."""
        return managed_browser_context(self, headless=headless, url=url)
