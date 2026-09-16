"""
Extractor for document_type == "restaurant_menu".

Uses the generic table_parser (see table_parser.py / pdf_layout.py) —
NO hardcoded column names. Whatever columns a given menu section has
(Item/Description/Vegetarian/Price, or Item/Type/Price, or anything
else) come through as-is.

Known, disclosed limitation: `restaurant_name` cannot be determined
from a single table page in a multi-page menu — that information
typically lives on a different page (e.g. a "Restaurant Overview"
page). PDFConnector currently processes each page independently with
no memory of other pages, so this field is left None rather than
guessed from the page's own section heading (which is NOT the
restaurant's name, just this page's section title).
"""

import re
from typing import Any, Dict

from document_intelligence.table_parser import auto_detect_table

SECTION_TITLE_PREFIX = re.compile(r"^\d+\.\s*")


def extract(cleaned_text: str, lines_text: str) -> Dict[str, Any]:
    lines = [l for l in lines_text.splitlines() if l.strip()]
    section_title = SECTION_TITLE_PREFIX.sub("", lines[0]).strip() if lines else "Menu"

    rows = auto_detect_table(lines)

    return {
        "document_type": "restaurant_menu",
        # Not derivable from a single page — see module docstring.
        "restaurant_name": None,
        "categories": [{"name": section_title, "items": rows}] if rows else [],
    }
