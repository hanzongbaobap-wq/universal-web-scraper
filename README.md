# universal-web-scraper

Production-grade Python web scraper template: polite, retry-safe, and outputs clean CSV/Excel.

Built and maintained by a senior software engineer (ex-IBM, ex-Accenture, 10+ years).
Available for custom scraping work on Upwork.

## Features

- ✅ Retry with exponential backoff (network hiccups won't kill your run)
- ✅ User-Agent rotation + realistic headers (basic anti-blocking)
- ✅ Polite crawling: configurable delay between requests, respects `robots.txt`
- ✅ Structured output: CSV and Excel in one run
- ✅ Logging to file + console summary (run stats in 3 lines)

## Quick Start

```bash
pip install requests beautifulsoup4 pandas openpyxl
python scraper.py --url "https://books.toscrape.com/" --pages 3 --out data/books
```

## Configuration

Edit `TARGETS` in `scraper.py` or pass CLI args:

| Arg | Description | Default |
|---|---|---|
| `--url` | Start URL | required |
| `--pages` | Max pages to crawl | 1 |
| `--delay` | Seconds between requests | 1.5 |
| `--out` | Output file prefix | `data/output` |

## Output

```
data/books.csv    # raw structured rows
data/books.xlsx   # same data, formatted for humans
logs/scraper.log  # full run log
```

## Legal & Ethics

Scrapes publicly available data only. Respects robots.txt. No login-walled or private data.

## License

MIT
