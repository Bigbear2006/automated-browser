import base64

from agents import ToolOutputImage, function_tool

from app.browser import BrowserService
from app.logging import logger

browser_service = BrowserService()


@function_tool
async def navigate_to(url: str) -> str:
    """Navigate browser to a URL."""
    return f'Current URL: {await browser_service.navigate(url)}'


@function_tool
async def get_page_snapshot() -> str:
    """Get current page accessibility snapshot with element references.

    The snapshot shows the page structure
    in YAML format with [ref=eX] references
    that can be used with other tools to interact with elements.
    """
    return await browser_service.get_snapshot()


@function_tool
async def click_element(ref: str) -> str:
    """
    Click an element by its reference.
    Reference can be:
    - 'e1', 'e2' ref from the snapshot;
    - element text from the snapshot;
    """
    result = await browser_service.click(ref)
    logger.info(f'[*] {result}')
    return result


@function_tool
async def type_into_element(ref: str, text: str) -> str:
    """Type text into an element by its reference."""
    result = await browser_service.type_text(ref, text)
    logger.info(f'[*] {result}')
    return result


@function_tool
async def press_key_on_element(ref: str, key: str) -> str:
    """Press a keyboard key on an element.

    Args:
        ref: Element reference from the snapshot
        key: Key name (e.g., 'Enter', 'Tab', 'Escape', 'ArrowDown')

    Returns: message
    """
    result = await browser_service.press_key(ref, key)
    logger.info(f'[*] {result}')
    return result


@function_tool
async def get_current_url() -> str:
    return await browser_service.get_current_url()


@function_tool
async def wait(seconds: int) -> str:
    """Wait for given number of milliseconds.
    Use this ONLY IF page isn't loaded yet"""
    result = await browser_service.wait(seconds)
    logger.info(f'[*] {result}')
    return result


@function_tool
async def take_screenshot(filename: str = 'screenshot.png') -> ToolOutputImage:
    logger.info(f'[*] Take screenshot {filename}')
    img_bytes = await browser_service.screenshot(filename)
    return ToolOutputImage(
        image_url=f'data:image/png;base64,{base64.b64encode(img_bytes).decode("utf-8")}'
    )


@function_tool
async def create_tab(url: str = 'about:blank') -> str:
    """Create new tab in browser.
    Use this function if user explicitly asks you open new tab.
    Otherwise, you `navigate_to` tool
    """
    return await browser_service.create_tab(url)


@function_tool
async def get_all_tabs() -> str:
    """Get all tabs in browser. Returns every tab index, url and title"""
    return await browser_service.get_all_tabs()


@function_tool
async def get_active_tab_index() -> int:
    """Return active tab index"""
    return await browser_service.get_active_page_index()


@function_tool
async def switch_to_tab(index: int) -> str:
    """Switch tab with given index"""
    return await browser_service.switch_to_tab(index)


@function_tool
async def close_tab(index: int) -> str:
    """Close tab by index"""
    return await browser_service.close_tab(index)
