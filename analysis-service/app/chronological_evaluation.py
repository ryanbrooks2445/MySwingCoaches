"""Strict, evidence-weighted swing evaluation."""

from app.schemas import SwingMode

CHRONOLOGICAL_EVALUATION_FULL = """[FULL-SWING EVIDENCE RUBRIC — MANDATORY]

Analyze the entire swing in chronological order, then choose the PRIMARY priority by evidence weight.
Do not default to setup/posture. Setup is one candidate, not the automatic answer.

STEP 0 — FULL CHECKPOINT PASS (grade these before writing):

1) Setup
   - Grip if visible, posture, alignment, ball position, distance from ball, athletic balance.
   - Weight distribution: heels-heavy / chair-squat vs balanced mid-foot.

2) Takeaway
   - Clubface, hand path, arm structure, body rotation, early wrist set.

3) Backswing/top
   - Swing plane, shoulder turn, hip turn, trail elbow, lead arm, head movement, weight shift.

4) Transition
   - Sequencing, lower-body start, arm drop, shallowing/steepening, tempo.

5) Downswing
   - Swing path, clubface control, rotation through impact, early extension, head stability,
     arm position, low point control.

6) Impact
   - Face/path relationship, weight location, shaft lean, contact-quality indicators, body position.

7) Follow-through
   - Balance, extension, rotation finish, exit path.

STEP 1 — SETUP CHECK (important, but not automatic):

1) Feet & pressure
   - Are they squatting back on their heels like sitting in a chair, OR balanced on the balls of the feet / mid-foot?
   - Heels-heavy at address often forces a lunge forward in the downswing just to reach the ball.

2) Stance width
   - Athletically wide for driver / stable for iron, OR too narrow / unstable?

3) Posture hinge
   - Bending from the hips with athletic spine angle, OR slouching from the shoulders / rounded upper back?

Setup/posture can be the PRIMARY priority only when:
- It is clearly visible as a Constraint, AND
- It plausibly causes the later miss pattern, AND
- Later categories (path, clubface, sequencing, head movement, arm structure, impact) are less important or are mainly compensations.

If setup is only a minor imperfection but the clearest performance leak is path, face, sequencing, head movement,
arm structure, rotation, weight shift, or impact, choose that later category as the primary priority.

STEP 2 — TOP-OF-BACKSWING STRUCTURE CHECK (mandatory):

Grade these at the top checkpoint and store visible misses in diagnostic_checkpoints/evidence_metrics:
1) Lead arm structure
   - Relatively extended with useful width, OR clearly bent/collapsed across the chest?
   - If lead arm bend is visible, mention it in Setup to finish or Advanced Evidence even if setup remains the primary fix.

2) Width at the top
   - Hands have space away from the chest, OR arms collapse and narrow the swing arc?

3) Overswing / arm runoff
   - Body turn and arm swing stop together, OR arms keep going after the body stops?

If lead-arm bend/collapse, narrow width, or arm runoff is clear, include it in user-facing evidence or hidden evidence.
Do not bury obvious arm structure under a generic posture note.

STEP 3 — PRIORITY COMPARISON (required before selecting primary flaw):

Compare these candidates and choose the one with the strongest visible evidence and biggest impact on contact/direction:
posture/setup, grip, takeaway, swing path, clubface, head movement, arm structure, rotation, sequencing,
weight shift, impact position.

For each candidate you seriously considered, ask:
- What did I actually see on video or key frames?
- Is it a root cause or a downstream compensation?
- Would fixing this create the fastest next-upload improvement?
- Is this stronger than posture/setup evidence?

The report's main_fix MUST name the winning candidate. secondary_fix MUST name the next-most useful candidate.

DIVERSITY GUARD:
- If the prior swing had the same main priority, repeat it only when the new video has clear evidence for the same issue.
- If evidence is mixed or weak, choose the better-supported current-swing priority and say what changed.
- Never produce two posture/setup reports in a row unless setup evidence is clearly decisive in both videos.

USER-FACING COVERAGE REQUIREMENT:
- What's working: name 2-3 genuine strengths visible on film.
- Setup to finish: briefly mention setup, takeaway/backswing, transition/downswing, impact, and finish.
- Include observations for swing path, head movement, arm/hand path, and clubface when visible; if a camera angle blocks one, say it is limited in hidden evidence.
- MANDATORY CALL-OUTS: If lead arm clearly bends/collapses at the top OR weight fails to load/shift (stuck on trail, hang back),
  those MUST appear in user-facing text — flaw2/flaw3, Arm/hand structure section, or secondary_fix. Never skip an obvious top-of-backswing arm bend or missing weight transfer just because path or transition is the primary fix.
- Keep the final coaching simple: one primary flaw, one secondary flaw, one feel, one drill, one next-upload goal."""

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
