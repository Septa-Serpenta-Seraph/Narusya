STALE - was removed in skill consolidation pass
description: "All of Hermes' web skills (web_search, web_extract, web_scrape, etc.) in one skill. Use for web browsing, scraping, search, extraction, and data collection."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [web, web-search, web-scrape, extraction, web-scraper, web-scout]
    related_skills: []
---

# Web Skills

All of Hermes' web skills in one skill.

## Web Search

### web_search

Search the web using your configured backend. Returns up to 5 results with title, URL, and description.

```
from hermes_tools import web_search
web_search(query="example query", limit=5)
```

### web_scrape

Extract content from a web page URL. Returns page content as markdown.

```
from hermes_tools import web_scrape
web_scrape(url="https://example.com")
```

## Data Extraction

### web_extract

Extract content from multiple URLs (up to 10).

```
from hermes_tools import web_extract
web_extract(urls=["https://example.com/page1", "https://example.com/page2"])
```

## Scraping

### web_scout

Quickly scout web pages for key information.

### web_scrape

Scrape entire web pages with pagination support.

## Utilities

### web_sitemap

Extract and analyze web sitemaps.

### web_domains

Check domain availability and WHOIS info.

### web_images

Search and extract images from web pages.
