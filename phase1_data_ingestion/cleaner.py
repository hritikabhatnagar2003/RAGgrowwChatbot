"""
Phase 1.2.4 — Data Cleaning & Normalization Module
Cleans raw scraped text: removes boilerplate, normalizes encoding,
preserves table structures, deduplicates content.
"""

import hashlib
import html
import os
import re
import logging
import unicodedata

import config

# ── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def _unescape_html(text: str) -> str:
    """Unescape HTML entities like &amp;, &#8377;, &nbsp;, etc."""
    return html.unescape(text)


def _normalize_unicode(text: str) -> str:
    """Normalize Unicode to NFKD form and clean special chars."""
    text = unicodedata.normalize("NFKD", text)
    # Replace common problematic characters
    text = text.replace("\u00a0", " ")   # Non-breaking space
    text = text.replace("\u200b", "")    # Zero-width space
    text = text.replace("\u200c", "")    # Zero-width non-joiner
    text = text.replace("\u200d", "")    # Zero-width joiner
    text = text.replace("\ufeff", "")    # BOM
    return text


def _remove_boilerplate(text: str) -> str:
    """Remove known Groww boilerplate patterns from text."""
    lines = text.split("\n")
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()
        # Skip empty lines at this stage (we'll normalize whitespace later)
        if not stripped:
            cleaned_lines.append("")
            continue

        # Check if line contains any boilerplate pattern
        is_boilerplate = False
        for pattern in config.BOILERPLATE_PATTERNS:
            if pattern.lower() in stripped.lower():
                is_boilerplate = True
                break

        if not is_boilerplate:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def _remove_navigation_elements(text: str) -> str:
    """Remove common navigation text patterns from Groww pages."""
    # Patterns for navigation-like text
    nav_patterns = [
        r"(?m)^Home\s*[›>]\s*.*$",                    # Breadcrumb lines
        r"(?m)^Explore\s+(Stocks|Mutual Funds|IPO).*$", # Explore links
        r"(?m)^(Login|Sign Up|Sign In).*$",            # Auth links
        r"(?m)^(Stocks|F&O|Mutual Funds|US Stocks|IPO|ETFs|NPS)\s*$",  # Top nav items
        r"(?m)^(Calculators|Knowledge Centre|More)\s*$",  # Menu items
        r"(?m)^(SIP Calculator|SWP Calculator|Mutual Fund Returns Calculator)\s*$",
        r"(?m)^Direct plan.*Regular plan.*$",           # Plan comparison headers
        r"(?m)^(Start SIP|Invest|One-Time|Monthly SIP)\s*$",  # CTAs
    ]

    for pattern in nav_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    return text


def _normalize_whitespace(text: str) -> str:
    """Collapse excessive whitespace while preserving structure."""
    # Replace multiple spaces with single space (within lines)
    text = re.sub(r"[ \t]+", " ", text)
    # Replace 3+ consecutive newlines with 2 newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip trailing whitespace from each line
    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines)


def _deduplicate_paragraphs(text: str) -> str:
    """Remove duplicate paragraphs using hash-based fingerprinting."""
    paragraphs = text.split("\n\n")
    seen_hashes = set()
    unique_paragraphs = []

    for para in paragraphs:
        stripped = para.strip()
        if not stripped:
            continue

        # Hash the normalized paragraph
        para_hash = hashlib.md5(stripped.lower().encode()).hexdigest()

        if para_hash not in seen_hashes:
            seen_hashes.add(para_hash)
            unique_paragraphs.append(para)

    return "\n\n".join(unique_paragraphs)


def _remove_short_noise_lines(text: str) -> str:
    """Remove very short lines that are likely noise (buttons, icons, etc.)."""
    lines = text.split("\n")
    cleaned = []

    for line in lines:
        stripped = line.strip()
        # Keep empty lines (structural), markdown headings, list items, and table rows
        if (
            not stripped
            or stripped.startswith("#")
            or stripped.startswith("-")
            or stripped.startswith("|")
            or len(stripped) > 10
        ):
            cleaned.append(line)

    return "\n".join(cleaned)


def clean_document(raw_text: str) -> str:
    """
    Apply the full cleaning pipeline to a raw scraped document.

    Pipeline:
    1. HTML unescape
    2. Unicode normalization
    3. Remove boilerplate patterns
    4. Remove navigation elements
    5. Remove short noise lines
    6. Deduplicate paragraphs
    7. Normalize whitespace
    """
    text = raw_text

    text = _unescape_html(text)
    text = _normalize_unicode(text)
    text = _remove_boilerplate(text)
    text = _remove_navigation_elements(text)
    text = _remove_short_noise_lines(text)
    text = _deduplicate_paragraphs(text)
    text = _normalize_whitespace(text)

    # Final strip
    text = text.strip()

    return text


def clean_all() -> dict:
    """
    Clean all raw documents in data/raw/ and save to data/cleaned/.

    Returns:
        dict with keys: 'success' (list), 'warnings' (list of low-content docs)
    """
    config.ensure_directories()

    results = {"success": [], "warnings": []}

    raw_files = sorted([
        f for f in os.listdir(config.RAW_DIR)
        if f.endswith(".txt")
    ])

    if not raw_files:
        logger.warning("No raw files found in data/raw/. Run scraper first.")
        return results

    logger.info(f"Cleaning {len(raw_files)} raw documents...")

    for filename in raw_files:
        doc_id = filename.replace(".txt", "")
        raw_path = os.path.join(config.RAW_DIR, filename)
        cleaned_path = os.path.join(config.CLEANED_DIR, filename)

        logger.info(f"  Cleaning: {filename}")

        # Read raw text
        with open(raw_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        # Clean
        cleaned_text = clean_document(raw_text)

        # Validate content length
        if len(cleaned_text) < config.MIN_CONTENT_LENGTH:
            logger.warning(
                f"  ⚠ Low content after cleaning ({len(cleaned_text)} chars): {filename}"
            )
            results["warnings"].append(doc_id)

        # Save cleaned text
        with open(cleaned_path, "w", encoding="utf-8") as f:
            f.write(cleaned_text)

        logger.info(
            f"  ✓ {len(raw_text)} → {len(cleaned_text)} chars "
            f"({len(cleaned_text) / max(len(raw_text), 1) * 100:.0f}% retained)"
        )
        results["success"].append(doc_id)

    logger.info("=" * 60)
    logger.info(f"Cleaning complete!")
    logger.info(f"  ✓ Cleaned: {len(results['success'])}")
    logger.info(f"  ⚠ Warnings: {len(results['warnings'])}")

    return results


if __name__ == "__main__":
    clean_all()
