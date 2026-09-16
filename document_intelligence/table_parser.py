"""
Generic table parser for layout-preserved text (see pdf_layout.py).

No hardcoded column list needed -- columns come from the table's own
header row.

WRAPPED-CELL HANDLING -- this took two real fixes to get right:
  1st attempt: a mismatched-cell-count line ended the whole table.
  2nd attempt: mismatched lines were skipped -- looked like success
      but silently dropped wrapped continuation text.
  3rd attempt (this version): rather than counting cells per line,
      detect whether a line contains something aligned with the FIRST
      column (a new item starting) or not (a continuation of the
      current row). This handles the harder real-world case found via
      an actual PDF: a short cell (e.g. Price) vertically centered
      against a multi-line row can land on a LATER physical line, not
      the first -- so "first line has full cell count" is not a safe
      assumption. Every cell on every line is matched to its column by
      horizontal position and merged into whichever row is currently
      open.
"""

import re
from typing import Dict, List, Tuple

CELL_SPLIT = re.compile(r"\s{2,}")
FIRST_COL_TOLERANCE = 4   # chars; how close a cell must start to column 0 to count as "new row"
MAX_ITEM_LABEL_LENGTH = 40  # a genuine item/row label is short; longer text at that position is prose, not a new row


def split_row(line: str) -> List[str]:
    return [cell.strip() for cell in CELL_SPLIT.split(line.strip()) if cell.strip()]


def _split_row_with_positions(line: str) -> List[Tuple[int, str]]:
    """Like split_row(), but also returns each cell's starting character index."""
    seps = list(CELL_SPLIT.finditer(line))
    cells = []
    start = 0
    for sep in seps:
        text = line[start:sep.start()]
        stripped = text.strip()
        if stripped:
            offset = len(text) - len(text.lstrip())
            cells.append((start + offset, stripped))
        start = sep.end()
    tail = line[start:]
    stripped_tail = tail.strip()
    if stripped_tail:
        offset = len(tail) - len(tail.lstrip())
        cells.append((start + offset, stripped_tail))
    return cells


def normalize_key(label: str) -> str:
    key = re.sub(r"[^a-zA-Z0-9]+", "_", label.strip().lower())
    return key.strip("_") or "field"


def _merge_cells_into_row(row: Dict[str, str], header_positions: List[Tuple[int, str]], cells_with_pos: List[Tuple[int, str]]) -> None:
    for pos, text in cells_with_pos:
        nearest_key = min(header_positions, key=lambda hp: abs(hp[0] - pos))[1]
        if row.get(nearest_key):
            row[nearest_key] = f"{row[nearest_key]} {text}"
        else:
            row[nearest_key] = text


def auto_detect_table(lines: List[str]) -> List[Dict[str, str]]:
    """Returns a list of row dicts, keyed by the table's OWN column headers."""
    header: List[str] = None
    header_positions: List[Tuple[int, str]] = None
    rows: List[Dict[str, str]] = []
    current_row: Dict[str, str] = None

    for line in lines:
        cells_with_pos = _split_row_with_positions(line)

        if header is None:
            cells = [t for _, t in cells_with_pos]
            if len(cells) >= 2:
                header = [normalize_key(c) for c in cells]
                header_positions = [(pos, normalize_key(c)) for pos, c in cells_with_pos]
            continue

        if not cells_with_pos:
            continue  # blank line

        first_col_pos = header_positions[0][0]
        first_col_cell = next((text for pos, text in cells_with_pos if abs(pos - first_col_pos) <= FIRST_COL_TOLERANCE), None)
        starts_new_row = first_col_cell is not None and len(first_col_cell) <= MAX_ITEM_LABEL_LENGTH

        if not starts_new_row and current_row is None:
            continue  # nothing to attach this line to yet -- not in a table

        if not starts_new_row and len(line.strip()) > 80:
            break  # a long, non-aligned line -- genuinely left the table section

        if starts_new_row:
            if current_row is not None:
                rows.append(current_row)
            current_row = {}

        _merge_cells_into_row(current_row, header_positions, cells_with_pos)

    if current_row is not None:
        rows.append(current_row)

    return rows
