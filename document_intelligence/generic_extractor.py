"""
Generic, schema-free item extraction.

This REPLACES the earlier per-document-type extractor system
(extractor_registry.py + one extractor per type + schemas.py's
required-field lists). That system had a real flaw: it only attempted
table extraction for pages that first matched one of a handful of
hardcoded document categories. A page from a domain the classifier had
never seen (a sofa shop, a bank, anything) fell to "unknown" and never
even tried the table detector -- even when it had a perfectly good
table sitting right there.

This module always tries, in order, for EVERY page, regardless of
what document_type the classifier guesses:

    1. Table detection (table_parser.auto_detect_table) -- works for
       any visually-aligned table, whatever its columns are called.
    2. Price-anchored line-item detection -- for catalogs/listings
       written as prose rather than a clean table (e.g. "3-seater
       Oakwood sofa, beige, Rs 45,000" as a sentence, not a table row).
    3. Plain cleaned text -- if neither structure is found, at least
       return the readable text rather than nothing.

No field is ever required. No document type gets its own hardcoded
schema. Whatever a table's own header row says, or whatever an item
line contains, is what comes out.
"""

import re
from typing import Any, Dict, List

from document_intelligence.table_parser import auto_detect_table, split_row, normalize_key
from document_intelligence.field_extractor import extract_fields

PRICE_PATTERN = re.compile(
    r"(?:₹|Rs\.?|INR|\$|USD)\s?[\d,]+(?:\.\d{1,2})?"
)

# Matches a line (or a column-split segment of a line) shaped like
# "Label: value" -- e.g. "Invoice Number: INV-2024-1001",
# "Bill To: Globex Inc", "Effective Date: 02/19/2024". No fixed list of
# labels: whatever text precedes the colon becomes the field name.
KEY_VALUE_PATTERN = re.compile(r"^([A-Za-z][A-Za-z0-9 /&\-]{0,40}?):\s*(.+)$")


def _detect_key_value_pairs(lines: List[str]) -> Dict[str, str]:
    """
    Generic form-style field detector: finds every 'Label: value' line
    on the page (splitting a line first on wide column gaps, so two
    fields sharing one line -- e.g. "Email: x@y.com   Phone: 555-0111"
    -- are captured separately) and merges them into one flat record.
    Works for invoices, contracts, resumes, or any other document that
    happens to use this pattern, without knowing the field names ahead
    of time.
    """
    result: Dict[str, str] = {}
    for line in lines:
        segments = split_row(line) or [line.strip()]
        for segment in segments:
            match = KEY_VALUE_PATTERN.match(segment)
            if match:
                key = normalize_key(match.group(1))
                value = match.group(2).strip()
                if key and value:
                    result[key] = value
    return result


def _detect_price_anchored_items(lines: List[str]) -> List[Dict[str, Any]]:
    """
    Heuristic for prose-style catalogs with no visual table: a line
    that contains a price-like token is treated as one item; everything
    before the price on that line is treated as the item's description.
    Works regardless of exact wording, since it anchors on the price,
    not on any specific vocabulary.
    """
    items = []
    for line in lines:
        match = PRICE_PATTERN.search(line)
        if not match:
            continue
        price_text = match.group(0)
        description = line[:match.start()].strip(" -:,")
        if not description:
            continue
        items.append({"description": description, "price": price_text})
    return items


def extract(cleaned_text: str, lines_text: str) -> Dict[str, Any]:
    lines = [l for l in lines_text.splitlines() if l.strip()]

    methods_used = []
    items: List[Dict[str, Any]] = []

    # A real page often has BOTH a table (e.g. invoice line items) AND
    # surrounding key-value fields (invoice number, bill-to, totals) --
    # these are not mutually exclusive, so both are attempted and merged
    # rather than stopping at whichever succeeds first.
    table_rows = auto_detect_table(lines)
    if table_rows:
        items.extend(table_rows)
        methods_used.append("table")

    kv_pairs = _detect_key_value_pairs(lines)
    if kv_pairs:
        items.append(kv_pairs)
        methods_used.append("key_value_pairs")

    # Only try the loosest, most collision-prone strategy if nothing
    # more specific matched at all.
    if not items:
        prose_items = _detect_price_anchored_items(lines)
        if prose_items:
            items.extend(prose_items)
            methods_used.append("prose_price_anchor")

    if not items:
        # Nothing table-shaped, form-shaped, or price-list-shaped was
        # found. This is genuinely unstructured prose (a narrative
        # paragraph, an executive summary). Without an LLM, real
        # understanding (a summary, semantic meaning) isn't possible --
        # but pulling out any generic entities present, plus basic
        # stats, is still strictly more useful than a bare text dump.
        entities = extract_fields(cleaned_text)
        entities = {k: v for k, v in entities.items() if v}  # drop empty hits
        sentence_count = len([s for s in re.split(r"[.!?]+", cleaned_text) if s.strip()])
        word_count = len(cleaned_text.split())

        return {
            "extraction_method": "prose_stats",
            "item_count": 0,
            "items": [],
            "text": cleaned_text,
            "entities_found": entities,
            "word_count": word_count,
            "sentence_count": sentence_count,
        }

    return {
        "extraction_method": "+".join(methods_used),
        "item_count": len(items),
        "items": items,
    }
