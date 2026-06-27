"""Ultra-minimal flat schema for Gemini structured output.

Short property names and no nesting — Gemini rejects large constraint state spaces.
Blueprint/roadmap/disclaimer are applied server-side in report_converter.py.
Coach letter fields use title|detail pipe format (same as drills).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PhaseObservation(BaseModel):
    club: str = ""
    body: str = ""
    not_visible: str = ""


class SwingObservations(BaseModel):
    setup: PhaseObservation = Field(default_factory=PhaseObservation)
    takeaway: PhaseObservation = Field(default_factory=PhaseObservation)
    backswing: PhaseObservation = Field(default_factory=PhaseObservation)
    transition: PhaseObservation = Field(default_factory=PhaseObservation)
    downswing: PhaseObservation = Field(default_factory=PhaseObservation)
    impact: PhaseObservation = Field(default_factory=PhaseObservation)
    finish: PhaseObservation = Field(default_factory=PhaseObservation)


class PhaseGrade(BaseModel):
    grade: Literal["Optimal", "Compensating", "Constraint", "Not Visible"] = "Not Visible"
    reason: str = ""


class SwingGrades(BaseModel):
    setup: PhaseGrade = Field(default_factory=PhaseGrade)
    takeaway: PhaseGrade = Field(default_factory=PhaseGrade)
    backswing: PhaseGrade = Field(default_factory=PhaseGrade)
    transition: PhaseGrade = Field(default_factory=PhaseGrade)
    downswing: PhaseGrade = Field(default_factory=PhaseGrade)
    impact: PhaseGrade = Field(default_factory=PhaseGrade)
    finish: PhaseGrade = Field(default_factory=PhaseGrade)


class GeminiReportOut(BaseModel):
    """All fields optional with empty defaults; drills use 'name|why|how' pipe format."""

    model_config = ConfigDict(extra="ignore")

    observations: SwingObservations | None = None
    camera_angle: Literal["face-on", "down-the-line", "behind", "unclear"] = "unclear"
    video_usability: Literal["good", "acceptable", "poor"] = "poor"
    usability_note: str = ""
    grades: SwingGrades | None = None
    report_mode: Literal["maintenance", "development"] | None = None
    foundational_missing_piece: str = ""
    secondary_fix: str = ""
    miss_pattern_match: Literal["high", "medium", "low"] | None = None
    miss_conflict_note: str = ""

    greeting: str = ""
    rating: str = ""
    categories: list[str] = Field(default_factory=list, max_length=6)
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
    checkpoints: list[str] = Field(default_factory=list, max_length=14)
    root: str = ""
    secondary: str = ""
    symptom: str = ""
    evidence: list[str] = Field(default_factory=list, max_length=8)
    chain: str = ""
    confidence: float = 0.75
    focus: str = ""
    day7: str = ""
    letter_open: str = ""
    letter_headline: str = ""
    strength1: str = ""
    strength2: str = ""
    strength3: str = ""
    flaw1: str = ""
    flaw2: str = ""
    flaw3: str = ""
    ceiling_now: str = ""
    ceiling_unlock: str = ""
    fix1: str = ""
    fix2: str = ""
    fix3: str = ""
    body_cue: str = ""
    space_cue: str = ""


_LETTER_STRING_FIELDS = (
    "letter_open",
    "letter_headline",
    "strength1",
    "strength2",
    "strength3",
    "flaw1",
    "flaw2",
    "flaw3",
    "ceiling_now",
    "ceiling_unlock",
    "fix1",
    "fix2",
    "fix3",
    "body_cue",
    "space_cue",
)

_PHASE_OBSERVATION_SCHEMA = {
    "type": "object",
    "properties": {
        "club": {"type": "string"},
        "body": {"type": "string"},
        "not_visible": {"type": "string"},
    },
    "required": ["club", "body", "not_visible"],
}

_PHASE_GRADE_SCHEMA = {
    "type": "object",
    "properties": {
        "grade": {
            "type": "string",
            "enum": ["Optimal", "Compensating", "Constraint", "Not Visible"],
        },
        "reason": {"type": "string"},
    },
    "required": ["grade", "reason"],
}

GEMINI_RESPONSE_JSON_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "observations": {
            "type": "object",
            "properties": {
                "setup": _PHASE_OBSERVATION_SCHEMA,
                "takeaway": _PHASE_OBSERVATION_SCHEMA,
                "backswing": _PHASE_OBSERVATION_SCHEMA,
                "transition": _PHASE_OBSERVATION_SCHEMA,
                "downswing": _PHASE_OBSERVATION_SCHEMA,
                "impact": _PHASE_OBSERVATION_SCHEMA,
                "finish": _PHASE_OBSERVATION_SCHEMA,
            },
            "required": [
                "setup",
                "takeaway",
                "backswing",
                "transition",
                "downswing",
                "impact",
                "finish",
            ],
        },
        "camera_angle": {
            "type": "string",
            "enum": ["face-on", "down-the-line", "behind", "unclear"],
        },
        "video_usability": {"type": "string", "enum": ["good", "acceptable", "poor"]},
        "usability_note": {"type": "string"},
    },
    "required": ["observations", "camera_angle", "video_usability", "usability_note"],
}

GEMINI_COACHING_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "greeting": {"type": "string"},
        "rating": {"type": "string"},
        "categories": {"type": "array", "items": {"type": "string"}, "maxItems": 6},
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
        "checkpoints": {"type": "array", "items": {"type": "string"}, "maxItems": 14},
        "root": {"type": "string"},
        "secondary": {"type": "string"},
        "symptom": {"type": "string"},
        "evidence": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
        "chain": {"type": "string"},
        "confidence": {"type": "number"},
        "focus": {"type": "string"},
        "day7": {"type": "string"},
        "letter_open": {"type": "string"},
        "letter_headline": {"type": "string"},
        "strength1": {"type": "string"},
        "strength2": {"type": "string"},
        "strength3": {"type": "string"},
        "flaw1": {"type": "string"},
        "flaw2": {"type": "string"},
        "flaw3": {"type": "string"},
        "ceiling_now": {"type": "string"},
        "ceiling_unlock": {"type": "string"},
        "fix1": {"type": "string"},
        "fix2": {"type": "string"},
        "fix3": {"type": "string"},
        "body_cue": {"type": "string"},
        "space_cue": {"type": "string"},
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
        "secondary",
        "symptom",
        "evidence",
        "chain",
        "confidence",
        "focus",
        "day7",
        "letter_open",
        "letter_headline",
        "strength1",
        "strength2",
        "flaw1",
        "flaw2",
        "flaw3",
        "ceiling_now",
        "ceiling_unlock",
        "fix1",
        "fix2",
        "body_cue",
        "space_cue",
    ],
}


DIAGNOSTIC_RESPONSE_JSON_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "grades": {
            "type": "object",
            "properties": {
                "setup": _PHASE_GRADE_SCHEMA,
                "takeaway": _PHASE_GRADE_SCHEMA,
                "backswing": _PHASE_GRADE_SCHEMA,
                "transition": _PHASE_GRADE_SCHEMA,
                "downswing": _PHASE_GRADE_SCHEMA,
                "impact": _PHASE_GRADE_SCHEMA,
                "finish": _PHASE_GRADE_SCHEMA,
            },
            "required": [
                "setup",
                "takeaway",
                "backswing",
                "transition",
                "downswing",
                "impact",
                "finish",
            ],
        },
        "report_mode": {"type": "string", "enum": ["maintenance", "development"]},
        "foundational_missing_piece": {"type": "string"},
        "secondary_fix": {"type": "string"},
        "miss_pattern_match": {"type": "string", "enum": ["high", "medium", "low"]},
        "miss_conflict_note": {"type": "string"},
        "confidence": {"type": "number"},
    },
    "required": [
        "grades",
        "report_mode",
        "foundational_missing_piece",
        "secondary_fix",
        "miss_pattern_match",
        "miss_conflict_note",
        "confidence",
    ],
}
