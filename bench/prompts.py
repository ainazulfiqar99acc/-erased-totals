"""Prompt arms and output schemas. Frozen at preregistration (2026-10-11).

Schema field descriptions are deliberately neutral: they never mention abstaining, so the
only difference between BASE and PERMIT is the one PERMIT sentence in the prompt text.
"""

import hashlib
import json

import pydantic


class TotalAnswer(pydantic.BaseModel):
    total: str = pydantic.Field(description="The total amount on the document.")
    confidence: float = pydantic.Field(description="Confidence that the answer is exactly right, 0-100.")


class VisibilityProbe(pydantic.BaseModel):
    total_fully_visible: bool
    total_computable_from_visible_amounts: bool


class SumAnswer(pydantic.BaseModel):
    line_sum: str = pydantic.Field(description="The sum of the listed amounts.")
    confidence: float = pydantic.Field(description="Confidence that the answer is exactly right, 0-100.")


BASE = (
    "This is a photo of a bill or receipt. What is the total amount on it "
    "(the final total / amount due)?\n"
    "Respond in JSON with two fields:\n"
    '- "total": the total amount\n'
    '- "confidence": how confident you are that your total is exactly right, from 0 to 100'
)

PERMIT = BASE + '\nIf the total cannot be determined from the image, set "total" to "UNREADABLE".'

PROBE = (
    "This is a photo of a bill or receipt. Look at its final total / amount due.\n"
    "Respond in JSON with two fields:\n"
    '- "total_fully_visible": true if the numeric value of the total is fully visible and '
    "legible in the image, otherwise false\n"
    '- "total_computable_from_visible_amounts": true if the exact total could be calculated '
    "from other amounts that are fully visible on the document, otherwise false"
)

SUMCAP = (
    "This is a photo of a bill or receipt. Do not use the total line. Add up every individual "
    "amount listed above the total (each item, charge, fee and tax line).\n"
    "Respond in JSON with two fields:\n"
    '- "line_sum": the sum of those amounts\n'
    '- "confidence": how confident you are that your sum is exactly right, from 0 to 100'
)

# arm -> list of (prompt text, schema, send image with this turn)
ARMS = {
    "BASE": [(BASE, TotalAnswer, True)],
    "PERMIT": [(PERMIT, TotalAnswer, True)],
    "PROBE": [(PROBE, VisibilityProbe, True)],
    "TWOPASS": [(PROBE, VisibilityProbe, True), (PERMIT, TotalAnswer, False)],
    "SUMCAP": [(SUMCAP, SumAnswer, True)],
}

# arm -> conditions it runs on, per split (preregistration §4)
COVERAGE = {
    "pilot": {
        "BASE": None,  # None = every condition in the split
        "PERMIT": None,
        "PROBE": None,
        "TWOPASS": ["D100", "N100"],
        "SUMCAP": ["D100"],
    },
    "main": {
        "BASE": None,
        "PERMIT": None,
        "PROBE": None,
        "TWOPASS": ["D50", "D100", "N50", "N100"],
        "SUMCAP": ["D100"],
    },
}
COVERAGE["smoke"] = {"BASE": None}
# Deadline core for the main split (Deviation 6): every item the confirmatory analysis uses
# (H1, H2, S1, S2, S3, S4, V1, V2). Same cache keys as the full run, so the rest can be added later.
COVERAGE["main_core"] = {
    "BASE": ["clean", "D0", "D100", "N50", "N100"],
    "PERMIT": ["D100", "N100"],
    "PROBE": ["N100"],
    "TWOPASS": ["D100", "N100"],
    "SUMCAP": ["D100"],
}
# Real-scan add-on (CORD; Deviation 5).
COVERAGE["cord"] = {"BASE": None, "PROBE": ["N100"], "TWOPASS": ["D100", "N100"]}


def arm_fingerprint(arm: str) -> str:
    """Hash of everything that defines an arm's requests; part of every cache key."""
    turns = [
        dict(text=text, schema=schema.model_json_schema(), image=image)
        for text, schema, image in ARMS[arm]
    ]
    return hashlib.sha256(json.dumps(turns, sort_keys=True).encode()).hexdigest()[:16]
