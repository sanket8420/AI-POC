"""
Basic document classification.

For a POC we use a transparent, explainable keyword-scoring approach
rather than a black-box ML model — this is intentional: it's easy to
demo, easy to extend, and easy to swap out later for a real ML/LLM-based
classifier without changing anything else in the pipeline (the connector
just calls classify_document() and gets a label back either way).
"""

from typing import Dict, List, Tuple

# Each category maps to a set of keywords that tend to appear in it.
# Scoring = number of keyword hits found in the (lower-cased) text.
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "invoice": ["invoice", "invoice number", "amount due", "bill to", "subtotal", "tax", "total due"],
    "contract": ["agreement", "hereby", "parties", "terms and conditions", "effective date", "signature"],
    "resume": ["experience", "education", "skills", "resume", "curriculum vitae", "objective"],
    # "report" and "policy" are merged into one category per the current spec's
    # "Policy/Report" document type.
    "policy_report": [
        "executive summary", "quarter", "findings", "analysis", "revenue",
        "policy", "guidelines", "compliance", "procedure", "this policy",
    ],
    "restaurant_menu": [
        "menu", "appetizer", "starter", "entree", "entr\u00e9e", "dessert",
        "beverage", "price", "prix fixe",
    ],
    "student_records": [
        "student", "grade", "section", "enrollment", "roll number",
        "attendance", "school record", "gpa", "student id",
    ],
}

# Renamed from "unclassified" to match the required contract: unmatched
# documents must be labeled exactly "unknown".
DEFAULT_LABEL = "unknown"

# Minimum distinct keyword hits required before trusting a label. A
# single incidental word match (e.g. "policy" inside "policies", "menu"
# inside an unrelated sentence, "education" inside "education loan")
# is not enough evidence — this was found via real false-positive
# misclassifications on unrelated banking-domain content.
MIN_HITS_FOR_CONFIDENT_LABEL = 2


def classify_document(text: str) -> Tuple[str, float]:
    """
    Returns (label, confidence) where confidence is a simple 0-1 score
    based on relative keyword-match strength across categories.
    """
    if not text:
        return DEFAULT_LABEL, 0.0

    lowered = text.lower()
    scores = {
        category: sum(1 for kw in keywords if kw in lowered)
        for category, keywords in CATEGORY_KEYWORDS.items()
    }

    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]

    if best_score < MIN_HITS_FOR_CONFIDENT_LABEL:
        return DEFAULT_LABEL, 0.0

    total_hits = sum(scores.values()) or 1
    confidence = round(best_score / total_hits, 2)
    return best_category, confidence
