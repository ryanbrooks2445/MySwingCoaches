"""Strict chronological swing evaluation — setup before downswing symptoms."""

from app.schemas import SwingMode

CHRONOLOGICAL_EVALUATION_FULL = """[CHRONOLOGICAL EVALUATION RULE — MANDATORY]

Analyze the swing in STRICT chronological order. A later-phase miss is almost always caused by an earlier error.
Grade and coach from the ground up. Never jump to downswing path fixes if setup is broken.

STEP 0 — THE GROUND-UP SETUP CHECK (do this FIRST, before takeaway/transition/downswing):

1) Feet & weight distribution
   - Are they squatting back on their heels like sitting in a chair, OR balanced on the balls of the feet / mid-foot?
   - Heels-heavy at address often forces a lunge forward in the downswing just to reach the ball.

2) Stance width
   - Athletically wide for driver / stable for iron, OR too narrow / unstable?

3) Posture hinge
   - Bending from the hips with athletic spine angle, OR slouching from the shoulders / rounded upper back?

If ANY setup item is Constraint, that is your foundational_missing_piece until proven otherwise on film.

THE CAUSE-AND-EFFECT LINK (user-facing copy when setup drives downstream issues):
- You MUST connect setup to what happens later. Example pattern:
  "Because your weight started stuck back on your heels at setup, your body naturally had to lunge forward
  during the swing just to reach the ball."
- Adapt the exact words to what you see (heels, narrow stance, poor hinge, ball position) — do not copy blindly.

ZERO JUMPING AHEAD:
- If setup or stance is broken, at least 80% of tips_and_feels and drills must fix feet, balance, and posture.
- Do NOT assign complex path drills (back_to_target, alignment_stick_shallow) when address is the root.
- In Setup to finish, describe **Setup** before blaming **Downswing** or path.

foundational_missing_piece naming examples:
- "Heel-heavy setup causing forward lunge"
- "Narrow stance / unstable base at address"
- "Shoulder slouch instead of hip hinge"
Only use transition/OTT/steep path language when setup grades Optimal or Compensation only."""

CHRONOLOGICAL_EVALUATION_CHIP = """[CHRONOLOGICAL EVALUATION — CHIPPING]

Order: Setup (weight forward, landing spot) → backswing length → hinge → strike → finish.
If setup is broken (weight back, no landing spot, ball position wrong), 80% of feels/drills fix setup first.
Do not coach full-swing path faults on a chip."""

CHRONOLOGICAL_EVALUATION_PUTT = """[CHRONOLOGICAL EVALUATION — PUTTING]

Order: Setup (eyes, posture, aim) → backstroke → tempo → forward stroke → impact.
If setup is broken, 80% of feels/drills fix setup and start line before blaming "read" or face-only fixes."""


def chronological_evaluation_for_prompt(swing_mode: SwingMode = "full_swing") -> str:
    if swing_mode == "chipping":
        return CHRONOLOGICAL_EVALUATION_CHIP
    if swing_mode == "putting":
        return CHRONOLOGICAL_EVALUATION_PUTT
    return CHRONOLOGICAL_EVALUATION_FULL


def setup_is_primary_constraint(foundational_missing_piece: str | None, main_fix: str | None) -> bool:
    """True when diagnosis points to address/feet/posture — triggers setup-first drill bias."""
    text = f"{foundational_missing_piece or ''} {main_fix or ''}".lower()
    setup_signals = (
        "setup",
        "address",
        "heel",
        "stance",
        "posture",
        "hinge",
        "balance",
        "feet",
        "launchpad",
        "slouch",
        "narrow",
        "lunge",
        "weight distribution",
        "ball position",
    )
    return any(s in text for s in setup_signals)
