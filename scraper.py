#!/usr/bin/env python3
"""universal-web-scraper — production-grade template scraper.

Polite, retry-safe web scraping with CSV + Excel output.
Demo target: books.toscrape.com (a site built for scraping practice).
Replace parse() to fit your target site's HTML structure.
"""
import argparse
import itertools
import logging
import random
import sys
import time
from urllib.parse import urljoin
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

LOG_FILE = Path("logs/scraper.log")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)  # create before logging init
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("scraper")


def fetch(session: requests.Session, url: str, delay: float, max_retries: int = 4) -> str | None:
    """GET with UA rotation, exponential backoff, and polite delay."""
    for attempt in range(1, max_retries + 1):
        headers = {"User-Agent": random.choice(USER_AGENTS), "Accept-Language": "en-US,en;q=0.9"}
        try:
            resp = session.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                return resp.text
            if resp.status_code in (403, 429):
                wait = 2**attempt + random.random()
                log.warning("HTTP %s on %s — backing off %.1fs (attempt %d/%d)", resp.status_code, url, wait, attempt, max_retries)
                time.sleep(wait)
                continue
            resp.raise_for_status()
        except requests.RequestException as exc:
            wait = 2**attempt
            log.warning("Request failed (%s) — retry in %.0fs (attempt %d/%d)", exc, wait, attempt, max_retries)
            time.sleep(wait)
    log.error("Giving up on %s after %d attempts", url, max_retries)
    return None


def parse(html: str) -> list[dict]:
    """Extract rows from a listing page. ADAPT THIS to your target site."""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for item in soup.select("article.product_pod"):
        rows.append(
            {
                "title": item.h3.a.get("title", "").strip(),
                "price": item.select_one("p.price_color").get_text(strip=True),
                "availability": item.select_one("p.instock.availability").get_text(strip=True),
                "url": item.h3.a.get("href", ""),
            }
        )
    return rows


def crawl(start_url: str, pages: int, delay: float) -> pd.DataFrame:
    session = requests.Session()
    all_rows: list[dict] = []
    url = start_url
    for page_no in itertools.count(1):
        if page_no > pages:
            break
        log.info("Page %d: %s", page_no, url)
        html = fetch(session, url, delay)
        if html is None:
            break
        rows = parse(html)
        all_rows.extend(rows)
        log.info("  +%d rows (total %d)", len(rows), len(all_rows))
        soup = BeautifulSoup(html, "html.parser")
        next_link = soup.select_one("li.next a")
        if not next_link:
            log.info("No next page — done.")
            break
        url = urljoin(url, next_link.get("href", ""))  # handles relative paths correctly
        time.sleep(delay)
    return pd.DataFrame(all_rows)


def main() -> None:
    ap = argparse.ArgumentParser(description="Universal polite web scraper")
    ap.add_argument("--url", required=True, help="Start URL")
    ap.add_argument("--pages", type=int, default=1, help="Max pages to crawl")
    ap.add_argument("--delay", type=float, default=1.5, help="Seconds between requests")
    ap.add_argument("--out", default="data/output", help="Output file prefix")
    args = ap.parse_args()

    Path("logs").mkdir(exist_ok=True)
    df = crawl(args.url, args.pages, args.delay)
    if df.empty:
        log.error("No data extracted — check parse() against the site's HTML.")
        sys.exit(1)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(f"{out}.csv", index=False, encoding="utf-8-sig")
    df.to_excel(f"{out}.xlsx", index=False)
    log.info("DONE: %d rows -> %s.csv / %s.xlsx", len(df), out, out)


if __name__ == "__main__":
    main()
