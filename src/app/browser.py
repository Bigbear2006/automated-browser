from contextlib import asynccontextmanager

from playwright.async_api import (
    Browser,
    BrowserContext,
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
        page = await self.get_active_page()
        snapshot = await page.locator('body').aria_snapshot(
            mode='ai', depth=depth
        )
        return snapshot

    async def navigate(self, url: str) -> str | None:
        page = await self.get_active_page()
        rsp = await page.goto(url)
        return rsp.url if rsp else None

    async def click(self, ref: str) -> bool:
        page = await self.get_active_page()

        try:
            # Try using locator with aria attributes first
            locator = page.locator(
                f"[data-aria-ref='{ref}'], [aria-ref='{ref}']"
            )
            count = await locator.count()

            if count > 0:
                await locator.first.click()
            else:
                # Fallback: extract index and click from interactive elements
                ref_num = int(ref[1:]) if ref.startswith('e') else 0
                elements = await page.query_selector_all(
                    "button, a[href], input[type='button'], "
                    "input[type='submit'], textarea, select, "
                    "[role='button'], [role='link']"
                )
                if ref_num < len(elements):
                    await elements[ref_num].click()
                else:
                    raise ValueError(f'Element {ref} not found')
        except Exception as e:
            raise ValueError(f'Could not click element {ref}: {str(e)}') from e

        return True

    async def type_text(self, ref: str, text: str) -> bool:
        page = await self.get_active_page()

        try:
            # Try aria attributes first
            locator = page.locator(
                f"[data-aria-ref='{ref}'], [aria-ref='{ref}']"
            )
            count = await locator.count()

            if count > 0:
                await locator.first.fill(text)
            else:
                # Fallback: use index approach
                ref_num = int(ref[1:]) if ref.startswith('e') else 0
                inputs = await page.query_selector_all('input, textarea')
                if ref_num < len(inputs):
                    await inputs[ref_num].fill(text)
                else:
                    raise ValueError(f'Input element {ref} not found')
        except Exception as e:
            raise ValueError(
                f'Could not type into element {ref}: {str(e)}'
            ) from e

        return True

    async def press_key(self, ref: str, key: str) -> bool:
        page = await self.get_active_page()

        try:
            locator = page.locator(
                f"[data-aria-ref='{ref}'], [aria-ref='{ref}']"
            )
            count = await locator.count()

            if count > 0:
                await locator.first.press(key)
            else:
                ref_num = int(ref[1:]) if ref.startswith('e') else 0
                elements = await page.query_selector_all(
                    "input, textarea, button, a, [role='button']"
                )
                if ref_num < len(elements):
                    await elements[ref_num].press(key)
                else:
                    raise ValueError(f'Element {ref} not found')
        except Exception as e:
            raise ValueError(
                f'Could not press key on element {ref}: {str(e)}'
            ) from e

        return True

    async def get_current_url(self) -> str:
        page = await self.get_active_page()
        logger.info(f'[*] Get current URL: {page.url}')
        return page.url

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

    async def get_elements(self) -> str:
        logger.info('[*] Get elements')
        # ruff: disable[E501]
        SNAPSHOT_JS = """
        () => {
          let counter = 0;
          const nextId = () => 'e' + (++counter);

          function isVisible(el) {
            const rect = el.getBoundingClientRect();
            if (rect.width === 0 || rect.height === 0) return false;
            const style = getComputedStyle(el);
            return style.visibility !== 'hidden' && style.display !== 'none';
          }

          function accessibleName(el) {
            return (
              el.getAttribute('aria-label') ||
              el.labels?.[0]?.innerText ||
              el.getAttribute('placeholder') ||
              el.getAttribute('title') ||
              el.innerText ||
              el.getAttribute('name') ||
              ''
            ).trim().slice(0, 100);
          }

          function classSignature(el) {
            const classes = Array.from(el.classList).sort().join('.');
            return el.tagName + (classes ? '.' + classes : '');
          }

          function tagId(el, id) {
            el.setAttribute('data-agent-id', id);
          }

          const BUTTON_SEL = 'button, [role="button"], input[type="submit"], input[type="button"], a[href]';
          const INPUT_SEL = 'input:not([type="submit"]):not([type="button"]), textarea, select, [contenteditable="true"]';

          // ---------- 1. Кнопки ----------
          const buttons = [];
          document.querySelectorAll(BUTTON_SEL).forEach(el => {
            if (!isVisible(el)) return;
            const id = nextId();
            tagId(el, id);
            buttons.push({
              id,
              tag: el.tagName.toLowerCase(),
              text: accessibleName(el),
              href: el.getAttribute('href') || undefined,
            });
          });

          // ---------- 2. Инпуты ----------
          const inputs = [];
          document.querySelectorAll(INPUT_SEL).forEach(el => {
            if (!isVisible(el)) return;
            const id = nextId();
            tagId(el, id);
            inputs.push({
              id,
              tag: el.tagName.toLowerCase(),
              type: el.getAttribute('type') || (el.tagName === 'SELECT' ? 'select' : 'text'),
              name: el.getAttribute('name') || undefined,
              label: accessibleName(el),
              value: el.value || undefined,
            });
          });

          // ---------- 3. Поиск повторяющихся групп (списки/карточки) ----------
          const groups = [];
          const usedElements = new Set();
          const allEls = document.querySelectorAll('body *');

          for (const parent of allEls) {
            if (parent.children.length < 3) continue;
            if (!isVisible(parent)) continue;

            const buckets = {};
            for (const child of parent.children) {
              if (!isVisible(child)) continue;
              if (child.classList.length === 0) continue;
              const sig = classSignature(child);
              (buckets[sig] = buckets[sig] || []).push(child);
            }

            for (const sig in buckets) {
              const items = buckets[sig];
              if (items.length < 3) continue;
              // пропускаем, если эти элементы уже вошли в другую (более внешнюю) группу
              if (items.some(el => usedElements.has(el))) continue;

              items.forEach(el => usedElements.add(el));

              const groupItems = items.slice(0, 20).map(el => {
                const itemId = nextId();
                tagId(el, itemId);

                const innerButtons = [];
                el.querySelectorAll(BUTTON_SEL).forEach(b => {
                  if (!isVisible(b)) return;
                  const bid = nextId();
                  tagId(b, bid);
                  innerButtons.push({ id: bid, text: accessibleName(b) });
                });

                const innerInputs = [];
                el.querySelectorAll(INPUT_SEL).forEach(i => {
                  if (!isVisible(i)) return;
                  const iid = nextId();
                  tagId(i, iid);
                  innerInputs.push({ id: iid, type: i.getAttribute('type') || 'text', label: accessibleName(i) });
                });

                return {
                  id: itemId,
                  text: (el.innerText || '').trim().slice(0, 150),
                  buttons: innerButtons,
                  inputs: innerInputs,
                };
              });

              groups.push({
                group_id: 'g' + (groups.length + 1),
                signature: sig,
                total_count: items.length,
                shown_count: groupItems.length,
                items: groupItems,
              });
            }
          }

          // ---------- 4. Одиночные значимые блоки (не попавшие в группы) ----------
          const singles = [];
          const SINGLE_SEL = 'h1, h2, h3, [role="heading"], header, nav, main, footer, [role="alert"], [role="dialog"]';
          document.querySelectorAll(SINGLE_SEL).forEach(el => {
              if (!isVisible(el)) return;
              if (usedElements.has(el)) return;
              const text = (el.innerText || '').trim().slice(0, 150);
              if (!text) return;
              const id = nextId();
              tagId(el, id)
              singles.push({ id, tag: el.tagName.toLowerCase(), role: el.getAttribute('role') || undefined, text });
          });
          return { buttons, inputs, groups, singles };
        }"""
        # ruff: enable[E501]
        page = await self.get_active_page()
        return await page.evaluate(SNAPSHOT_JS)

    def managed_browser(
        self, headless: bool = False, url: str = 'about:blank'
    ):
        """Return context manager for browser lifecycle."""
        return managed_browser_context(self, headless=headless, url=url)
