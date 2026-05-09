"""
Phase 1.2.3 — Web Scraper Module
Scrapes HDFC Mutual Fund scheme pages from Groww using Playwright (headless browser).
Handles JS-rendered SPA content, retries, and edge cases.
"""

import json
import os
import random
import time
import logging
from datetime import date
from urllib.parse import quote

from bs4 import BeautifulSoup

import config

# ── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def load_manifest(manifest_path: str = None) -> list[dict]:
    """Load the URL manifest from urls.json."""
    path = manifest_path or config.URLS_MANIFEST
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_manifest(manifest: list[dict], manifest_path: str = None):
    """Save the updated manifest back to urls.json (with last_accessed dates)."""
    path = manifest_path or config.URLS_MANIFEST
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def _encode_url(url: str) -> str:
    """
    Handle special characters in URLs (e.g., apostrophe in HDFC Children's Fund).
    Playwright handles most encoding, but we sanitize just in case.
    """
    # Only encode the path portion if there's an apostrophe
    if "'" in url:
        parts = url.split("/mutual-funds/")
        if len(parts) == 2:
            encoded_slug = quote(parts[1], safe="-")
            return parts[0] + "/mutual-funds/" + encoded_slug
    return url


def _extract_tables_as_markdown(soup: BeautifulSoup) -> str:
    """
    Convert HTML tables to markdown format to preserve tabular data structure.
    This runs before the main text extraction.
    """
    markdown_tables = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue

        md_rows = []
        for i, row in enumerate(rows):
            cells = row.find_all(["th", "td"])
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            md_row = "| " + " | ".join(cell_texts) + " |"
            md_rows.append(md_row)

            # Add header separator after first row
            if i == 0:
                separator = "| " + " | ".join(["---"] * len(cell_texts)) + " |"
                md_rows.append(separator)

        markdown_tables.append("\n".join(md_rows))
        # Replace the HTML table with a placeholder
        table.replace_with(f"\n\n{''.join(md_rows)}\n\n")

    return "\n\n".join(markdown_tables)


def _extract_page_content(page_html: str, url: str) -> str:
    """
    Extract meaningful content from a Groww mutual fund scheme page.
    Preserves headings, paragraphs, lists, and tables.
    """
    soup = BeautifulSoup(page_html, "html.parser")

    # Remove script, style, nav, footer, and other non-content elements
    for tag in soup.find_all(["script", "style", "nav", "footer", "header",
                              "noscript", "iframe", "svg", "link", "meta"]):
        tag.decompose()

    # Remove elements that are typically navigation/boilerplate
    for selector in [
        "[class*='navbar']", "[class*='Navbar']",
        "[class*='footer']", "[class*='Footer']",
        "[class*='sidebar']", "[class*='Sidebar']",
        "[class*='cookie']", "[class*='Cookie']",
        "[class*='banner']",
        "[class*='appDownload']", "[class*='AppDownload']",
        "[class*='signUp']", "[class*='SignUp']",
        "[id*='nav']", "[id*='footer']",
    ]:
        for element in soup.select(selector):
            element.decompose()

    # Convert remaining tables to markdown before text extraction
    _extract_tables_as_markdown(soup)

    # Extract text with structure preservation
    content_parts = []

    # Try to find the main content area
    main_content = (
        soup.find("main")
        or soup.find("div", {"id": "app"})
        or soup.find("div", {"id": "root"})
        or soup.find("div", {"class": lambda x: x and "content" in x.lower()})
        or soup.body
        or soup
    )

    if main_content:
        # Walk through elements and preserve structure
        for element in main_content.find_all(
            ["h1", "h2", "h3", "h4", "h5", "h6", "p", "div", "span",
             "li", "td", "th", "section", "article"]
        ):
            text = element.get_text(separator=" ", strip=True)
            if not text or len(text) < 3:
                continue

            # Add heading markers
            if element.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                level = int(element.name[1])
                prefix = "#" * level
                content_parts.append(f"\n{prefix} {text}\n")
            elif element.name == "li":
                content_parts.append(f"- {text}")
            else:
                content_parts.append(text)

    # Deduplicate consecutive identical lines (common with nested divs)
    deduped = []
    for part in content_parts:
        if not deduped or part != deduped[-1]:
            deduped.append(part)

    full_text = "\n".join(deduped)

    # Add source metadata header
    header = f"Source: {url}\nDate Accessed: {date.today().isoformat()}\n{'=' * 60}\n\n"

    return header + full_text


def scrape_page_playwright(url: str, page, timeout_ms: int = None) -> str:
    """
    Scrape a single Groww page using a Playwright page instance.
    Waits for the JS-rendered content to load.
    """
    timeout = timeout_ms or config.SCRAPE_TIMEOUT_MS
    encoded_url = _encode_url(url)

    logger.info(f"  Navigating to: {encoded_url}")
    page.goto(encoded_url, wait_until="networkidle", timeout=timeout)

    # Wait for the main content to render (Groww-specific selectors)
    try:
        page.wait_for_selector(
            "div[class*='fund'], div[class*='scheme'], div[class*='mutual'], h1",
            timeout=15000,
        )
    except Exception:
        logger.warning(f"  Content selector not found, proceeding with available content")

    # Give extra time for lazy-loaded content
    page.wait_for_timeout(2000)

    # Get the full rendered HTML
    html_content = page.content()

    return _extract_page_content(html_content, url)


def scrape_all(manifest: list[dict] = None) -> dict:
    """
    Scrape all URLs from the manifest using Playwright.

    Returns:
        dict with keys: 'success' (list of doc_ids), 'failed' (list of doc_ids),
                        'warnings' (list of doc_ids with low content)
    """
    from playwright.sync_api import sync_playwright

    if manifest is None:
        manifest = load_manifest()

    config.ensure_directories()

    results = {"success": [], "failed": [], "warnings": []}

    with sync_playwright() as p:
        # Launch browser with a random user agent
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=random.choice(config.USER_AGENTS),
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()

        for i, entry in enumerate(manifest):
            doc_id = entry["doc_id"]
            url = entry["url"]
            scheme_name = entry["scheme_name"]

            logger.info(f"[{i + 1}/{len(manifest)}] Scraping: {scheme_name}")

            retries = 0
            success = False

            while retries < config.MAX_RETRIES and not success:
                try:
                    content = scrape_page_playwright(url, page)

                    # Content length validation
                    if len(content) < config.MIN_CONTENT_LENGTH:
                        logger.warning(
                            f"  ⚠ Low content ({len(content)} chars) for {scheme_name}"
                        )
                        results["warnings"].append(doc_id)

                    # Save raw text
                    raw_path = os.path.join(config.RAW_DIR, f"{doc_id}.txt")
                    with open(raw_path, "w", encoding="utf-8") as f:
                        f.write(content)

                    # Update last_accessed in manifest
                    entry["last_accessed"] = date.today().isoformat()

                    logger.info(
                        f"  ✓ Saved {len(content)} chars → {raw_path}"
                    )
                    results["success"].append(doc_id)
                    success = True

                except Exception as e:
                    retries += 1
                    wait_time = (2 ** retries) + random.uniform(0, 1)
                    logger.error(
                        f"  ✗ Attempt {retries}/{config.MAX_RETRIES} failed: {e}"
                    )
                    if retries < config.MAX_RETRIES:
                        logger.info(f"  Retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                        # Rotate user agent on retry
                        context.close()
                        context = browser.new_context(
                            user_agent=random.choice(config.USER_AGENTS),
                            viewport={"width": 1920, "height": 1080},
                        )
                        page = context.new_page()

            if not success:
                logger.error(f"  ✗ FAILED after {config.MAX_RETRIES} retries: {scheme_name}")
                results["failed"].append(doc_id)

            # Polite delay between requests
            if i < len(manifest) - 1:
                delay = config.SCRAPE_DELAY_SECONDS + random.uniform(0, 2)
                logger.info(f"  Waiting {delay:.1f}s before next request...")
                time.sleep(delay)

        context.close()
        browser.close()

    # Save updated manifest with last_accessed dates
    save_manifest(manifest)

    # Summary
    logger.info("=" * 60)
    logger.info(f"Scraping complete!")
    logger.info(f"  ✓ Success: {len(results['success'])}")
    logger.info(f"  ⚠ Warnings: {len(results['warnings'])}")
    logger.info(f"  ✗ Failed:  {len(results['failed'])}")
    if results["failed"]:
        logger.info(f"  Failed IDs: {results['failed']}")

    return results


if __name__ == "__main__":
    scrape_all()
