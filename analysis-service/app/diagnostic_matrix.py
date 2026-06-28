"""Master diagnostic taxonomy for the Adaptive Mobility & Improvement Engine."""

from app.chronological_evaluation import chronological_evaluation_for_prompt
from app.mode_coaching import (
    PILLAR_3_PUTTING,
    PILLAR_3_SHORT_GAME,
    maintenance_criteria_block,
    pillar_2_for_mode,
    prioritization_block,
)
from app.schemas import SwingMode

# Internal grades only — never show numeric scores to users.
GRADE_LABELS = "Optimal | Compensation | Constraint | Not_visible"

REFERENCE_STANDARD_FULL_SWING = """REFERENCE STANDARD — what "Optimal" / 10-out-of-10 means on our rubric
(There is NO single reference video or tour-pro clip. Gemini grades each phase against this mechanical intent.)

SETUP — Optimal: athletic mid-foot pressure, hip hinge (not chair-squat on heels), stable stance width, arms hang naturally.

TAKEAWAY — Optimal: club, hands, and chest move together; no early wrist roll that shuts the face; arms stay in front of the body.

TOP OF BACKSWING — Optimal:
- Lead arm mostly extended with useful width (not collapsed across the chest)
- Hands have space away from the chest; club not sucked excessively inside
- Shoulder turn loads the backswing; hips turn (not just lateral sway)
- Weight / pressure loads into the trail side — not 50/50 or stuck on the lead foot going back

TRANSITION — Optimal: lower body starts down while arms shallow/drop; no snatch from the top; chest stays over the ball.

DOWNSWING / IMPACT — Optimal: path and face work together; hips clear; shaft lean at impact; low point ahead of the ball.

WEIGHT TRANSFER — Optimal:
- Backswing loads trail side; downswing shifts pressure to lead side through impact
- NOT hanging back on the trail foot, NOT reverse-pivoting, NOT stuck with weight on the trail side at the ball

FINISH — Optimal: full rotation, balance on lead side, chest facing target.

USER-FACING 10/10 RATING maps to maintenance mode: almost all visible checkpoints Optimal, at most one minor Compensation,
no Constraint chain. A 7/10 is NOT "good enough" — it means one major leak with several compensations still in play.
Athletic speed, a balanced finish, or good tempo do NOT earn high marks if arm structure, weight shift, or contact chain is broken."""

PILLAR_1_HUMAN = """PILLAR 1 — THE HUMAN BLUEPRINT (intake profile — apply BEFORE video)
- T-spine mobility: can the chest rotate or is it locked (forces arm lift)?
- Hip internal/external rotation: tight hips → lateral sway vs clean rotation
- Hamstring/core strength: weak core → early extension or standing up
- Injury & pain workarounds: back, knees, wrist/elbow, shoulder — adapt ALL cues
- Age & athletic background: fast-twitch vs safe spatial cheats for distance
- Years playing: beginner = foundations; 20-year vet = micro-adjustments, protect confidence"""

PILLAR_3_KINETIC = """PILLAR 3 — THE KINETIC CHAIN (full swing — chronological)

A) Takeaway & backswing (loading the spring)
- Thoracic rotation vs arm lift ("fake shoulder turn")
- Sway vs turn (lateral slide off ball vs spine-axis rotation)
- Wrist cock/hinge vs early cast
- Lead arm structure at top: extended width vs clear bend/collapse
- Swing depth & width at top: hands away from chest vs narrow/collapsed arc
- Arm runoff / overswing: arms keep going after body turn stops

B) Transition & downswing (unleashing power)
- Sequencing: ground-up (hips→torso→arms→club) vs top-down (arms first)
- Shallow vs steep / slot vs over-the-top
- Lag retention vs casting/scooping

C) Impact & release (moment of truth)
- Early extension (hips thrust toward ball, spine stands up)
- Low point control (chunk vs thin)
- Face-to-path relationship (start line + curve axis)

D) Finish (resultant truth)
- Weight transfer to lead foot vs hanging back
- Balance & posture in finish facing target"""

PILLAR_4_TEMPO = """PILLAR 4 — INTERNAL RHYTHMS (full swing tempo & flow)
- Backswing:downswing tempo ratio (~3:1 ideal for smooth power)
- Transition tension: smooth pause at top vs snatching down"""

PILLAR_4_CHIPPING = """PILLAR 4 — CHIPPING TEMPO & INTENT
- Backswing length proportional to landing spot distance
- Decel vs acceleration through strike (decel = fat/thin)
- Rhythm: shorter backswing + crisp through vs long back + stab"""

PILLAR_4_PUTTING = """PILLAR 4 — PUTTING TEMPO
- Backstroke length controls distance
- Smooth tempo (~2:1 back to forward for many players)
- No hitch at transition; accelerate through impact"""


def _diagnostic_workflow(swing_mode: SwingMode) -> str:
    prioritization = prioritization_block(swing_mode)
    maintenance_extra = maintenance_criteria_block(swing_mode)

    return f"""
ADAPTIVE MOBILITY & IMPROVEMENT ENGINE — MANDATORY INTERNAL WORKFLOW

Before writing ANY user-facing text, run this diagnostic pass:

{chronological_evaluation_for_prompt(swing_mode)}

STEP 1 — Read Pillar 1 (Human Blueprint) from player profile. Set physical ceilings.

STEP 2 — Watch the video IN CHRONOLOGICAL ORDER (setup first). For each relevant checkpoint below, assign ONE internal grade:
[{GRADE_LABELS}]
- Optimal: matches intent for their body and goals
- Compensation: athletic workaround for an earlier link in the chain
- Constraint: physical or setup limit driving compensations
- Not_visible: camera angle or quality prevents grading

STEP 3 — Choose report_mode (CRITICAL — do not force a flaw):

Set advanced_details.report_mode to "maintenance" OR "development".

USE "maintenance" only when the motion on film is already elite / tour-caliber / textbook:
- Zero Constraint grades on visible checkpoints, AND
- At most ONE minor Compensation, AND
- At least 90% of visible graded checkpoints are Optimal, AND
- Setup, transition, impact, and finish are all clearly visible and Optimal, AND
- No visible miss on film (NEVER invent slice/fade/hook/chunk/skull/push/pull unless you SEE it), AND
- You cannot name one practical improvement a good in-person coach would give this golfer.
{maintenance_extra}

USE "development" when there IS a real earliest Constraint or Compensation chain to unlock.

If unsure between "solid but coachable" and maintenance, choose development with a medium confidence note.
Reserve maintenance for clearly elite / tour-caliber motion on visible checkpoints. Great motion gets praise,
but a paid analysis should still name the most useful visible improvement when the swing is not clearly elite.

STEP 3b — PRIORITIZATION (development mode only):
{prioritization}

STEP 3c — MAINTENANCE mode (no forced flaw):
- foundational_missing_piece = "None — maintain current elite baseline"
{maintenance_extra}
- main_fix = what to KEEP doing, not what to change
- Drills = optional reinforcement/preservation, not beginner corrective drills

STEP 4 — Store in advanced_details:
- report_mode (maintenance or development)
- foundational_missing_piece, profile_constraints_applied, diagnostic_checkpoints (pipe-delimited strings),
  chain_reaction, root_cause, symptom, evidence_metrics, confidence_score, next_checkpoint

STEP 5 — User-facing copy (Athletic Upside tone):
- NEVER output grade labels to the user
- NEVER invent ball flight or misses not visible on film
- pga_analysis MUST include **Setup to finish** for both modes using MODE-SPECIFIC phase labels
- DEVELOPMENT: section titles The missing piece + What changes when you unlock it (plain text, no #)
- MAINTENANCE: section titles What to keep doing + Your ceiling at this level (no "missing piece" section)
- main_fix matches report_mode (unlock vs keep-owning)
- Do NOT paste generic full-swing OTT/steep/early-extension story onto chip/putt or elite swings
"""


def diagnostic_matrix_for_prompt(swing_mode: SwingMode = "full_swing") -> str:
    if swing_mode == "putting":
        kinetic = PILLAR_3_PUTTING
        tempo = PILLAR_4_PUTTING
    elif swing_mode == "chipping":
        kinetic = PILLAR_3_SHORT_GAME
        tempo = PILLAR_4_CHIPPING
    else:
        kinetic = PILLAR_3_KINETIC
        tempo = PILLAR_4_TEMPO

    return f"""{_diagnostic_workflow(swing_mode)}

{REFERENCE_STANDARD_FULL_SWING if swing_mode == "full_swing" else ""}

MASTER COVERAGE MAP (grade internally; do not dump this list to the user):

This is not a diagnosis menu and not a recommendation list. Use it only to make sure you inspect
the whole motion. The actual diagnosis must come from what is visible in this specific swing video.

{PILLAR_1_HUMAN}

{pillar_2_for_mode(swing_mode)}

{kinetic}

{tempo}
"""
