import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

from app.logging_conf import get_logger

logger = get_logger(__name__)

CRAWLER_USER_AGENT = "FashionAnalystBot/0.1 (+https://example.com/bot-info)"
MIN_SECONDS_BETWEEN_REQUESTS_PER_DOMAIN = 3.0

_robots_cache: dict[str, RobotFileParser] = {}
_last_request_at: dict[str, float] = {}


async def _fetch_robots(domain: str) -> RobotFileParser:
    parser = RobotFileParser()
    robots_url = f"https://{domain}/robots.txt"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(robots_url, headers={"User-Agent": CRAWLER_USER_AGENT})
        if response.status_code == 200:
            parser.parse(response.text.splitlines())
        else:
            parser.parse([])  # no robots.txt -> permissive default
    except httpx.HTTPError:
        logger.warning("robots_fetch_failed", domain=domain)
        parser.parse([])
    return parser


async def is_allowed(url: str) -> bool:
    domain = urlparse(url).netloc
    if domain not in _robots_cache:
        _robots_cache[domain] = await _fetch_robots(domain)
    return _robots_cache[domain].can_fetch(CRAWLER_USER_AGENT, url)


async def wait_for_rate_limit(url: str) -> None:
    domain = urlparse(url).netloc
    last = _last_request_at.get(domain, 0.0)
    elapsed = time.monotonic() - last
    if elapsed < MIN_SECONDS_BETWEEN_REQUESTS_PER_DOMAIN:
        import asyncio

        await asyncio.sleep(MIN_SECONDS_BETWEEN_REQUESTS_PER_DOMAIN - elapsed)
    _last_request_at[domain] = time.monotonic()


async def guard(url: str) -> bool:
    """Call before every fetch: enforces robots.txt + per-domain rate limiting.

    Returns False (and the caller must skip the fetch) if disallowed by robots.txt.
    """
    if not await is_allowed(url):
        logger.info("robots_disallowed", url=url)
        return False
    await wait_for_rate_limit(url)
    return True
