from abc import ABC, abstractmethod

from agents import FunctionTool
from playwright.async_api import BrowserContext, Page

from app.browser_manager import BrowserManager


class BaseAgentTools(ABC):
    def __init__(self, browser_manager: BrowserManager) -> None:
        self.browser_manager = browser_manager

    @property
    def context(self) -> BrowserContext:
        return self.browser_manager.context

    async def get_active_page(self) -> Page:
        return await self.browser_manager.get_active_page()

    @abstractmethod
    def get_all(self) -> list[FunctionTool]: ...
