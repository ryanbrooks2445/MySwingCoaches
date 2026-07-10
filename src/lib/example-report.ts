import type { SimplifiedSwingReport } from "@/lib/types";

/** Static anonymized report for the public /example marketing page. */
export const EXAMPLE_SIMPLIFIED_REPORT: SimplifiedSwingReport = {
  pga_analysis:
    "Your setup shows athletic posture with room to rotate, but pressure started too far toward the heels. That early balance pattern forced the body toward the ball in transition, which steepened the shaft and made it harder to clear the lead hip through impact.",
  main_fix: "Athletic setup balance — feel pressure under your laces before the takeaway so your spine angle stays stable through transition.",
  tips_and_feels: [
    "Feel pressure under your laces before the takeaway — not on your heels.",
    "Let the chest turn over a quiet head while the lead hip clears without standing up.",
  ],
  drills: [
    {
      name: "Athletic setup rehearsals",
      why_it_helps:
        "Trains centered pressure and hip hinge so transition does not pull you toward the ball.",
      how_to_do_it:
        "Take ten setup rehearsals with a club across your shoulders. Pause at address, feel laces pressure, then make fifteen half-speed shots checking the same feel.",
    },
  ],
  next_swing_check:
    "Confirm centered pressure and stable posture from face-on — head level through takeaway, no drift toward the ball in transition.",
  advanced_details: {
    report_mode: "development",
    foundational_missing_piece: "Centered setup pressure before rotation begins.",
    root_cause: "Heel-biased pressure at address limits hip hinge and pulls the body toward the ball later.",
    symptom: "Steepening shaft and early extension through the downswing window.",
    evidence_metrics: [
      "Setup: pressure appeared heel-heavy with spine angle set but limited room to rotate.",
      "Takeaway: clubhead stayed outside hands while upper body shifted toward the ball.",
      "Transition: lower body stalled briefly before hips cleared, steepening the shaft plane.",
      "Impact window: handle rushed, lead side braced late — ball flight not estimated on film.",
    ],
    secondary_fix: "Maintain width in the takeaway so the club does not lift steeply.",
    optional_fix: "Mirror check at address for hip hinge and knee flex symmetry.",
    chain_reaction:
      "Heel pressure → loss of posture in transition → steep shaft → compensatory early extension.",
    why_it_caused_the_miss:
      "When pressure starts on the heels, the body searches for balance by moving toward the ball, which steepens the path and reduces space through impact.",
    confidence_score: 0.82,
    diagnostic_checkpoints: [
      {
        checkpoint: "Setup:",
        grade: "constraint",
        observation: "Heel-heavy pressure with athletic posture but limited rotation room.",
      },
      {
        checkpoint: "Takeaway:",
        grade: "compensation",
        observation: "Clubhead outside hands; upper body drifted toward the ball.",
      },
      {
        checkpoint: "Backswing:",
        grade: "optimal",
        observation: "Shoulder turn reached a playable width without excessive arm lift.",
      },
      {
        checkpoint: "Transition:",
        grade: "constraint",
        observation: "Lower body started late; shaft steepened before hip clearing.",
      },
      {
        checkpoint: "Downswing:",
        grade: "compensation",
        observation: "Early extension visible as hips moved toward the ball.",
      },
      {
        checkpoint: "Impact:",
        grade: "not_visible",
        observation: "Ball not visible; impact geometry estimated from approach.",
      },
      {
        checkpoint: "Finish:",
        grade: "optimal",
        observation: "Balanced finish with full rotation despite earlier compensations.",
      },
    ],
  },
  coach_verdict: {
    overall_rating: "Developing",
    biggest_positive: "Athletic posture and a balanced finish show solid athleticism.",
    main_issue: "Setup pressure too far on the heels, forcing compensations later.",
    best_fix: "Center pressure under the laces before the takeaway.",
    category_ratings: [
      { label: "Setup", rating: "Needs work" },
      { label: "Backswing", rating: "Solid" },
      { label: "Downswing", rating: "Needs work" },
      { label: "Impact", rating: "Limited visibility" },
    ],
  },
  priority_fixes: [
    {
      rank: 1,
      phase: "Setup",
      title: "Athletic spine angle",
      issue:
        "Rounded upper spine (C-posture) at address restricts rotational capacity and sets up later posture loss.",
      why_first: "Root cause on film — every downstream compensation traces back to limited rotation room at address.",
      body_feels: [
        "Feel sternum over belt buckle — not a rounded upper back.",
        "Push chest toward the ball without arching the lower back.",
      ],
      space_feels: [
        "Room to turn without lifting your head.",
        "Keep steady space between chin and chest through the takeaway.",
      ],
      drill: {
        name: "Wall posture drill",
        why_it_helps: "Trains neutral spine at address so rotation does not require standing up.",
        how_to_do_it: "Upper back against a wall, hinge from hips, 10 rehearsal setups before hitting.",
      },
    },
    {
      rank: 2,
      phase: "Takeaway",
      title: "Club in front of hands",
      issue: "Clubhead moves outside the hands with a slightly closed face — a steep backswing setup.",
      why_first: "Common reaction to C-posture that steepens the backswing plane before transition.",
      body_feels: [
        "Feel hands staying under your sternum on the first move.",
        "Keep the toe from rolling open early.",
      ],
      space_feels: [
        "Clubhead stays in front of your trail shoulder until parallel.",
        "Width without lifting the club steeply.",
      ],
      drill: {
        name: "Headcover under trail arm",
        why_it_helps: "Prevents the roll-open takeaway that steepens the plane.",
        how_to_do_it: "10 half-speed takeaways keeping the headcover in place.",
      },
    },
    {
      rank: 3,
      phase: "Backswing",
      title: "Turn without standing up",
      issue: "Spine straightens and head lifts to complete the turn — laid-off club at the top.",
      why_first: "Direct compensation for the rotational limit set by setup posture.",
      body_feels: [
        "Feel your belt buckle turning while your head stays level.",
        "Lead arm stays long without lifting the shoulders.",
      ],
      space_feels: [
        "Club points at target line at the top — not laid off behind you.",
        "Maintain the spine angle you set at address.",
      ],
    },
    {
      rank: 4,
      phase: "Downswing",
      title: "Shallow the plane",
      issue: "Steep shaft forces over-the-top path and early extension to create space.",
      why_first: "Downstream of setup and takeaway — fix after earlier ranks hold on film.",
      body_feels: [
        "Feel lead hip clearing before hands drop.",
        "Stay in posture — hips rotate, not thrust toward the ball.",
      ],
      space_feels: [
        "Club drops into the slot from inside.",
        "Hands stay in front of chest through impact.",
      ],
    },
  ],
};
