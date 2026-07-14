from agents import function_tool

from src.app.browser import BrowserService

browser_service = BrowserService()


@function_tool
async def navigate_to(url: str) -> str:
    """Navigate browser to a URL."""
    return await browser_service.navigate(url)


@function_tool
async def get_page_snapshot() -> str:
    """Get current page accessibility snapshot with element references.

    The snapshot shows the page structure in YAML format with [ref=eX] references
    that can be used with other tools to interact with elements.
    """
    return await browser_service.get_snapshot()


@function_tool
async def click_element(ref: str) -> str:
    """Click an element by its reference from the snapshot.

    Args:
        ref: Element reference like 'e1', 'e2' from the snapshot

    Returns:
        Updated page snapshot after click
    """
    return await browser_service.click(ref)


@function_tool
async def type_into_element(ref: str, text: str) -> str:
    """Type text into an element by its reference.

    Args:
        ref: Element reference from the snapshot
        text: Text to type

    Returns:
        Updated page snapshot
    """
    return await browser_service.type_text(ref, text)


@function_tool
async def press_key_on_element(ref: str, key: str) -> str:
    """Press a keyboard key on an element.

    Args:
        ref: Element reference from the snapshot
        key: Key name (e.g., 'Enter', 'Tab', 'Escape', 'ArrowDown')

    Returns:
        Updated page snapshot
    """
    return await browser_service.press_key(ref, key)


@function_tool
async def get_current_url() -> str:
    """Get the current page URL."""
    return await browser_service.get_current_url()


@function_tool
async def take_screenshot(filename: str = 'screenshot.png') -> str:
    """Take a screenshot of the current page."""
    return await browser_service.screenshot(filename)
