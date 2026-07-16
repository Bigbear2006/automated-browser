from agents import FunctionTool, function_tool

from app.tools.base import BaseAgentTools


class NavigatorAgentTools(BaseAgentTools):
    def get_all(self) -> list[FunctionTool]:
        return [
            function_tool(func)
            for func in (
                self.get_current_url,
                self.navigate,
                self.create_tab,
                self.get_all_tabs,
                self.get_active_tab_index,
                self.switch_to_tab,
                self.close_tab,
            )
        ]

    async def get_current_url(self) -> str:
        """Get current page URL"""
        page = await self.get_active_page()
        return page.url

    async def navigate(self, url: str) -> str:
        """Navigate browser to a URL."""
        page = await self.get_active_page()
        await page.goto(url)
        return f'Current URL: {await self.get_current_url()}'

    async def create_tab(self, url: str = 'about:blank') -> str:
        """Create new tab in browser.
        Use this function if user explicitly asks you open new tab.
        Otherwise, you `navigate_to` tool"""
        page = await self.context.new_page()
        if url != 'about:blank':
            await page.goto(url)
        return f'Новая вкладка успешно создана. Текущий URL: {page.url}'

    async def get_all_tabs(self) -> str:
        """Get all tabs in browser. Returns every tab index, url and title"""
        pages = self.context.pages
        if not pages:
            return 'Нет открытых вкладок.'

        result = []
        for index, page in enumerate(pages):
            result.append(
                f'Индекс: {index} '
                f'| URL: {page.url} '
                f'| Заголовок: {await page.title()}'
            )
        return '\n'.join(result)

    async def get_active_tab_index(self) -> int:
        """Return active tab index"""
        page = await self.get_active_page()
        return self.context.pages.index(page)

    async def switch_to_tab(self, index: int) -> str:
        """Switch tab with given index (starts with 0)"""
        pages = self.context.pages
        if index < 0 or index >= len(pages):
            return (
                f'Ошибка: Вкладка с индексом {index} не найдена. '
                f'Всего вкладок: {len(pages)}'
            )

        await pages[index].bring_to_front()
        return f'Успешно переключено на вкладку {index}: {pages[index].url}'

    async def close_tab(self, index: int) -> str:
        """Close tab by index"""
        pages = self.context.pages
        if index < 0 or index >= len(pages):
            return (
                f'Ошибка: Невозможно закрыть. '
                f'Вкладка с индексом {index} не существует.'
            )

        url_closed = pages[index].url
        await pages[index].close()
        return f'Вкладка с индексом {index} ({url_closed}) успешно закрыта.'
