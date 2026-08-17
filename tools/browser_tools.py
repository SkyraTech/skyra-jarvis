"""
Jarvis Browser Tools — Phase 2B
=================================
Exposes browser automation capabilities to Gemini via function calling.
Calls the skyra-browser-service (port 8004) which runs Playwright.

Available tools:
  - browse_website     → Read a URL's content
  - search_the_web     → Google/Bing search and get results
  - extract_page_data  → Extract specific elements from a page
"""

from loguru import logger
from utils.network import call_local_api
from config import config

BROWSER_SERVICE_URL = config.BROWSER_SERVICE_URL


async def browse_website(url: str) -> str:
    """
    Open and read any website URL. Returns the page title and main content.
    Use this to research topics, read documentation, check competitor prices,
    or read any web page.

    Args:
        url: The full URL to browse (e.g. 'https://example.com')
    """
    logger.info(f"🌐 Tool Call: Browsing '{url}'...")
    success, data, err = await call_local_api("POST", f"{BROWSER_SERVICE_URL}/browse", {"url": url})

    if success:
        title = data.get("title", "No title")
        content = data.get("content", "")
        final_url = data.get("url", url)
        return (
            f"Page: {title}\n"
            f"URL: {final_url}\n\n"
            f"{content[:3000]}"
        )
    return f"Failed to browse '{url}': {err}"


async def search_the_web(query: str, engine: str = "google") -> str:
    """
    Search the web and return top results with titles, links, and snippets.
    Use this to find information, research topics, or discover resources.

    Args:
        query: The search query (e.g. 'best SaaS subscription pricing models 2026')
        engine: Search engine to use — 'google', 'bing', or 'duckduckgo' (default: google)
    """
    logger.info(f"🌐 Tool Call: Searching web for '{query}'...")
    success, data, err = await call_local_api(
        "POST",
        f"{BROWSER_SERVICE_URL}/search",
        {"query": query, "engine": engine}
    )

    if success:
        results = data.get("results", [])
        if not results:
            return f"No results found for '{query}'."
        lines = [f"Search results for: '{query}'\n"]
        for i, r in enumerate(results[:6], 1):
            lines.append(f"{i}. {r.get('title', 'No title')}")
            lines.append(f"   URL: {r.get('link', '')}")
            if r.get('snippet'):
                lines.append(f"   {r['snippet'][:200]}")
            lines.append("")
        return "\n".join(lines)
    return f"Search failed: {err}"


async def extract_page_data(url: str, css_selector: str = "") -> str:
    """
    Extract specific content from a web page using a CSS selector.
    If no selector is given, extracts the full page text.
    Use this to pull specific data like prices, tables, or specific sections.

    Args:
        url: The full URL to extract from
        css_selector: CSS selector of the element to extract (optional).
                      Example: 'table.pricing', '.price', '#main-content'
    """
    logger.info(f"🌐 Tool Call: Extracting data from '{url}' selector='{css_selector}'...")
    payload = {"url": url}
    if css_selector:
        payload["selector"] = css_selector

    success, data, err = await call_local_api("POST", f"{BROWSER_SERVICE_URL}/extract", payload)

    if success:
        content = data.get("content", "")
        return f"Extracted content from {url}:\n\n{content[:4000]}"
    return f"Failed to extract from '{url}': {err}"


async def take_browser_screenshot() -> str:
    """
    Take a screenshot of the current browser page.
    Returns a confirmation message. The screenshot is saved for review.
    Use this to visually verify what the browser is showing.
    """
    logger.info("🌐 Tool Call: Taking browser screenshot...")
    success, data, err = await call_local_api("POST", f"{BROWSER_SERVICE_URL}/screenshot", {})

    if success:
        current_url = data.get("current_url", "unknown page")
        return f"Screenshot taken of '{current_url}'. The browser is showing this page."
    return f"Screenshot failed: {err}"
