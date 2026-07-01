import hashlib
from dataclasses import dataclass

from playwright.async_api import async_playwright

from app.crawlers.robots import CRAWLER_USER_AGENT, guard
from app.logging_conf import get_logger

logger = get_logger(__name__)


@dataclass
class CrawledPage:
    url: str
    html: str
    content_hash: str
    status_code: int
    linked_urls: list[str]


async def crawl_page(url: str, wait_for_selector: str | None = None) -> CrawledPage | None:
    """Fetch a single JS-rendered page with Playwright. Returns None if robots.txt disallows it."""
    if not await guard(url):
        return None

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        try:
            page = await browser.new_page(user_agent=CRAWLER_USER_AGENT)
            response = await page.goto(url, wait_until="networkidle", timeout=30000)
            if wait_for_selector:
                await page.wait_for_selector(wait_for_selector, timeout=10000)

            html = await page.content()
            linked_urls = await page.eval_on_selector_all(
                "a[href]", "els => els.map(e => e.href)"
            )
            status_code = response.status if response else 0
        finally:
            await browser.close()

    content_hash = hashlib.sha256(html.encode("utf-8")).hexdigest()
    logger.info("crawled_page", url=url, status_code=status_code, bytes=len(html))
    return CrawledPage(
        url=url,
        html=html,
        content_hash=content_hash,
        status_code=status_code,
        linked_urls=linked_urls,
    )
