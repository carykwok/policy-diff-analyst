import hashlib
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from scripts.source_registry import is_allowed

USER_AGENT = "policy-diff-analyst/0.1 (+https://github.com/carykwok/policy-diff-analyst)"
TIMEOUT = 20

class FetchError(RuntimeError):
    pass

def _cache_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]

def fetch(url: str, cache_dir: Path) -> str:
    if not is_allowed(url):
        raise FetchError(f"URL not on whitelist: {url}")
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{_cache_key(url)}.txt"
    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8")
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        resp.raise_for_status()
    except Exception as e:
        raise FetchError(f"fetch failed for {url}: {e}") from e
    soup = BeautifulSoup(resp.content, "lxml")
    # Extract article body — fall back to whole text if no <article>
    article = soup.find("article") or soup.find("body")
    text = article.get_text("\n", strip=True) if article else soup.get_text("\n", strip=True)
    cache_file.write_text(text, encoding="utf-8")
    return text
