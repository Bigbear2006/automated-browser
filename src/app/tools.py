import base64
from collections.abc import Coroutine

from agents import ToolOutputImage, function_tool

from app.browser import BrowserService
from app.logging import logger

browser_service = BrowserService()


async def handle_tool_error(coro: Coroutine) -> dict[str, str | bool]:
    try:
        result = await coro
        return {'ok': result}
    except ValueError as e:
        return {'ok': False, 'message': str(e)}


@function_tool
async def navigate_to(url: str) -> dict[str, str | None]:
    """Navigate browser to a URL."""
    logger.info(f'[*] Navigate to {url}')
    return {'current_url': await browser_service.navigate(url)}


@function_tool
async def get_page_snapshot() -> str:
    """Get current page accessibility snapshot with element references.

    The snapshot shows the page structure
    in YAML format with [ref=eX] references
    that can be used with other tools to interact with elements.
    """
    logger.info('[*] Get page snapshot')
    return await browser_service.get_snapshot()


@function_tool
async def click_element(ref: str) -> dict[str, str | bool]:
    """Click an element by its reference (like 'e1', 'e2')
    from the snapshot."""
    logger.info(f'[*] Click element {ref}')
    return await handle_tool_error(browser_service.click(ref))


@function_tool
async def type_into_element(ref: str, text: str) -> dict[str, str | bool]:
    """Type text into an element by its reference."""
    logger.info(f'[*] Type {text} into element {ref}')
    return await handle_tool_error(browser_service.type_text(ref, text))


@function_tool
async def press_key_on_element(ref: str, key: str) -> dict[str, str | bool]:
    """Press a keyboard key on an element.

    Args:
        ref: Element reference from the snapshot
        key: Key name (e.g., 'Enter', 'Tab', 'Escape', 'ArrowDown')

    Returns:
        Updated ok (bool) and message (str)
    """
    logger.info(f'[*] Press key {key} on element {ref}')
    return await handle_tool_error(browser_service.press_key(ref, key))


@function_tool
async def get_current_url() -> str:
    logger.info('[*] Get current page URL')
    return await browser_service.get_current_url()


@function_tool
async def take_screenshot(filename: str = 'screenshot.png') -> ToolOutputImage:
    logger.info(f'[*] Take screenshot {filename}')
    img_bytes = await browser_service.screenshot(filename)
    return ToolOutputImage(
        image_url=f'data:image/png;base64,{base64.b64encode(img_bytes).decode("utf-8")}'
    )


@function_tool
async def get_page_elements() -> str:
    logger.info('[*] Get all page elements')
    return await browser_service.get_elements()


@function_tool
async def create_tab(url: str = 'about:blank') -> str:
    """Create new tab in browser"""
    return await browser_service.create_tab(url)


@function_tool
async def get_all_tabs() -> str:
    """Get all tabs in browser. Returns every tab index, url and title"""
    return await browser_service.get_all_tabs()


@function_tool
async def get_active_tab_index() -> int:
    return await browser_service.get_active_page_index()


@function_tool
async def switch_to_tab(index: int) -> str:
    return await browser_service.switch_to_tab(index)


@function_tool
async def close_tab(index: int) -> str:
    return await browser_service.close_tab(index)
