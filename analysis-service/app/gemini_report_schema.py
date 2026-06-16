"""Ultra-minimal flat schema for Gemini structured output.

Short property names and no nesting — Gemini rejects large constraint state spaces.
Blueprint/roadmap/disclaimer are applied server-side in report_converter.py.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class GeminiReportOut(BaseModel):
    """All fields optional with empty defaults; drills use 'name|why|how' pipe format."""

    model_config = ConfigDict(extra="ignore")

    greeting: str = ""
    analysis: str = ""
    main_fix: str = ""
    tips: list[str] = Field(default_factory=list, max_length=4)
    drill1: str = ""
    drill2: str = ""
    drill3: str = ""
    next_check: str = ""
    mode: str = "development"
    missing: str = ""
    profile: str = ""
    checkpoints: list[str] = Field(default_factory=list, max_length=10)
    root: str = ""
    symptom: str = ""
    evidence: list[str] = Field(default_factory=list, max_length=6)
    chain: str = ""
    confidence: float = 0.75
    focus: str = ""
    day7: str = ""


# Hand-tuned schema — shorter than Pydantic export, no $defs, no defaults on properties.
GEMINI_RESPONSE_JSON_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "greeting": {"type": "string"},
        "analysis": {"type": "string"},
        "main_fix": {"type": "string"},
        "tips": {"type": "array", "items": {"type": "string"}, "maxItems": 4},
        "drill1": {"type": "string"},
        "drill2": {"type": "string"},
        "drill3": {"type": "string"},
        "next_check": {"type": "string"},
        "mode": {"type": "string"},
        "missing": {"type": "string"},
        "profile": {"type": "string"},
        "checkpoints": {"type": "array", "items": {"type": "string"}, "maxItems": 10},
        "root": {"type": "string"},
        "symptom": {"type": "string"},
        "evidence": {"type": "array", "items": {"type": "string"}, "maxItems": 6},
        "chain": {"type": "string"},
        "confidence": {"type": "number"},
        "focus": {"type": "string"},
        "day7": {"type": "string"},
    },
    "required": [
        "greeting",
        "analysis",
        "main_fix",
        "tips",
        "next_check",
        "mode",
        "missing",
        "checkpoints",
        "root",
        "symptom",
        "evidence",
        "chain",
        "confidence",
        "focus",
        "day7",
    ],
}
