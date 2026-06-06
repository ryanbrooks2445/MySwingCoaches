"""Mode-specific coaching vocabulary, pillars, and workflow fragments."""

from app.schemas import SwingMode

SETUP_TO_FINISH_PHASES: dict[SwingMode, str] = {
    "full_swing": (
        "**Setup** · **Takeaway & backswing** · **Tempo & transition** · "
        "**Downswing** · **Impact & release** · **Finish**"
    ),
    "chipping": (
        "**Setup & landing spot** · **Backswing length** · **Hinge & low point** · "
        "**Strike & leading edge** · **Acceleration through** · **Finish & hold**"
    ),
    "putting": (
        "**Setup & eyes** · **Backstroke path** · **Tempo & pause** · "
        "**Forward stroke** · **Impact & face** · **Follow-through & head still**"
    ),
}

CHECKPOINT_VOCABULARY: dict[SwingMode, str] = {
    "full_swing": (
        "heels vs mid-foot pressure, stance width, hip hinge vs shoulder slouch, ball position, "
        "feet, balance, tempo, weight transfer, sequencing, lag, low point, face-to-path"
    ),
    "chipping": (
        "weight forward, ball position, landing spot, hinge amount, low point, leading edge vs bounce, "
        "hands ahead, strike crispness, acceleration (no decel), face at impact, finish height"
    ),
    "putting": (
        "eyes over ball, posture, grip pressure, stroke path (arc vs straight), backstroke length, "
        "tempo ratio, face angle at impact, start line, head stability, acceleration through"
    ),
}

PILLAR_2_FULL = """PILLAR 2 — THE STATIC LAUNCHPAD (setup — ALWAYS grade before takeaway; highest priority)

GROUND-UP SETUP CHECK (mandatory first on film):
- Weight distribution: heels-heavy / chair-squat vs balanced on balls of feet / mid-foot
- Stance width: athletic and stable for the club vs too narrow / wobbly
- Posture hinge: hip bend with spine angle vs shoulder slouch / rounded upper back
- Ball position, grip, alignment — only after the three checks above

If heels or poor hinge at address → expect downstream lunge, early extension, or steep compensations.
Name that cause-and-effect link explicitly in user-facing copy."""

PILLAR_2_CHIPPING = """PILLAR 2 — SHORT GAME SETUP (chip — highest priority)
- Stance: narrow, feet slightly open, weight 60–70% on lead foot
- Ball position: back of stance for low runner; middle for standard; slightly forward for higher loft
- Hinge preset: minimal hinge for bump-and-run; more hinge for lofted landing
- Landing spot chosen BEFORE the swing — commit to a spot on the green/fringe
- Grip: lighter than full swing; hands slightly ahead; face square or slightly open for loft
- Alignment: feet, hips, shoulders parallel to landing line (not always at pin)"""

PILLAR_2_PUTTING = """PILLAR 2 — PUTTING SETUP (highest priority)
- Eyes: over ball or slightly inside; consistent head position
- Posture: athletic bend, arms hang naturally, elbows soft
- Ball position: slightly forward of center for most strokes
- Grip: light pressure (3–4/10); palms oppose; no death grip
- Aim: putter face to start line; shoulders square to intended line
- Stance width: stable base; weight balanced mid-foot"""

PILLAR_3_SHORT_GAME = """PILLAR 3 — CHIPPING KINETIC CHAIN (chronological)

A) Setup & intent
- Weight forward maintained through strike
- Landing spot visualized; club selection matches lie and landing

B) Backswing & hinge
- Short, proportional backswing — length matches distance
- Wrist hinge amount matches shot (low vs high landing)
- No full-swing takeaway or excessive arm lift

C) Downswing & strike
- Low point ahead of ball; hands lead at impact
- Leading edge vs bounce usage for lie (tight vs fluffy)
- Acceleration through — decel causes chunks and skulls
- Stable body — minimal sway; rotation or body pivot as intended

D) Face & path at impact
- Face angle controls initial trajectory; path influences curve
- No scooping or flipping wrists through impact

E) Finish & distance control
- Finish low for runners; higher for soft landings
- Hold finish facing target; validate landing spot vs intent"""

PILLAR_3_PUTTING = """PILLAR 3 — PUTTING KINETIC CHAIN (chronological)

A) Setup & read
- Read matches start line intent; eyes and posture stable

B) Backstroke
- Path: slight arc or straight-back per setup
- Length controls distance — longer backstroke = more speed
- No jerk or lift at start of stroke

C) Transition & tempo
- Smooth change of direction — no pause-y hitch unless intentional
- Consistent tempo ratio (often ~2:1 back to forward)

D) Forward stroke & impact
- Accelerate through impact — do not decelerate
- Face square to intended start line at impact
- Putter path returns slightly inside (arc) or straight through

E) Follow-through & stability
- Head still through impact and early follow-through
- Finish matches backstroke length for distance control
- No steering with hands mid-stroke"""

PRIORITIZATION_BY_MODE: dict[SwingMode, str] = {
    "full_swing": (
        "CHRONOLOGICAL RULE: Grade Setup (feet/heels/stance/hinge) BEFORE takeaway or downswing.\n"
        "Walk backward: Setup → Backswing → Transition → Downswing → Impact → Finish.\n"
        "foundational_missing_piece = earliest Constraint — almost always setup if feet/posture are broken.\n"
        "If heels-heavy or poor hinge at address, write cause-and-effect: setup error CAUSED the downswing lunge/path.\n"
        "80% of tips_and_feels + drills must target feet/posture when setup is the root — no path drills yet."
    ),
    "chipping": (
        "Walk backward: Setup & landing intent → Backswing length → Hinge & low point → "
        "Strike (decel vs accelerate) → Face at impact → Finish.\n"
        "foundational_missing_piece = earliest chip Constraint — usually setup (weight, ball position, landing spot) "
        "before blaming 'technique.' Do NOT use OTT, lag, or full-swing transition language."
    ),
    "putting": (
        "Walk backward: Setup → Backstroke path/length → Tempo → Forward stroke → Face at impact → Head stability.\n"
        "foundational_missing_piece = earliest putting Constraint — setup and start line before blaming 'read.' "
        "Do NOT use backswing load, hip clearance, or full-swing sequencing language."
    ),
}

MAINTENANCE_CRITERIA_BY_MODE: dict[SwingMode, str] = {
    "full_swing": (
        "- No clear foundational breakdown in setup or backswing load\n"
        "- Do NOT assign steep path, OTT, early extension unless clearly visible AND graded Constraint"
    ),
    "chipping": (
        "- No clear breakdown in setup (weight forward, landing spot) or strike (decel, flip, fat/thin visible)\n"
        "- Do NOT assign full-swing faults (OTT, early extension, lag loss) to a crisp chip"
    ),
    "putting": (
        "- No clear breakdown in setup, start line, or tempo on film\n"
        "- Do NOT assign full-swing or chipping faults to a smooth putting stroke"
    ),
}

MODE_GUIDANCE: dict[SwingMode, str] = {
    "full_swing": """MODE: FULL SWING
Analyze address through finish. Use full-swing phase labels in Setup to finish.
Grade checkpoints: address, takeaway, top, downswing, impact, finish.
Never describe a chip or putt — this is a full golf swing with body rotation and power sequencing.""",
    "chipping": """MODE: CHIPPING (short game around the green)
This is NOT a full swing. Do NOT coach OTT, lag retention, hip clearance, or transition shallowing unless
the player is clearly making a full swing motion on a chip (rare — call that out if so).

Focus: landing spot, weight forward, hinge amount, low point, strike quality, acceleration through, finish height.
Use chip phase labels in Setup to finish (see prompt). Grade checkpoints: setup, backswing, downswing, impact, finish.
Distance control = backswing length + acceleration, not "swing harder."
Maintenance = crisp strike, committed landing spot, stable hinge — praise it.""",
    "putting": """MODE: PUTTING
This is a putting stroke on the green — no hip rotation power sequence, no ball flight curve coaching unless visible.

Focus: setup, eyes, stroke path, backstroke length, tempo, face at impact, start line, head still.
Use putting phase labels in Setup to finish (see prompt). Grade checkpoints: address, backstroke, forward, impact, follow_through, finish.
Never invent break or miss direction unless visible or stated.
Maintenance = repeatable tempo, stable face, quiet head — praise it.""",
}


def pillar_2_for_mode(swing_mode: SwingMode) -> str:
    if swing_mode == "chipping":
        return PILLAR_2_CHIPPING
    if swing_mode == "putting":
        return PILLAR_2_PUTTING
    return PILLAR_2_FULL


def setup_to_finish_block(swing_mode: SwingMode) -> str:
    phases = SETUP_TO_FINISH_PHASES.get(swing_mode, SETUP_TO_FINISH_PHASES["full_swing"])
    vocab = CHECKPOINT_VOCABULARY.get(swing_mode, CHECKPOINT_VOCABULARY["full_swing"])
    return (
        f"pga_analysis — In Setup to finish use these **bold phase labels** (exactly):\n{phases}\n\n"
        f"Name visible checkpoints when grading: {vocab}.\n"
        "If not visible: say \"hard to see on this angle\" — do not guess."
    )


def prioritization_block(swing_mode: SwingMode) -> str:
    return PRIORITIZATION_BY_MODE.get(swing_mode, PRIORITIZATION_BY_MODE["full_swing"])


def maintenance_criteria_block(swing_mode: SwingMode) -> str:
    return MAINTENANCE_CRITERIA_BY_MODE.get(swing_mode, MAINTENANCE_CRITERIA_BY_MODE["full_swing"])


def mode_guidance_block(swing_mode: SwingMode) -> str:
    guidance = MODE_GUIDANCE.get(swing_mode, MODE_GUIDANCE["full_swing"])
    return f"{guidance}\n\n{setup_to_finish_block(swing_mode)}"
