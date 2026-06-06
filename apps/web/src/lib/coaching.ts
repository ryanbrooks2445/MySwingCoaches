import type {
  AnalysisBullet,
  CoachSummaryReport,
  CoachingContent,
  FeelBlueprintDiagnostic,
  SwingDiagnosisEngine,
  SwingReport,
} from "@/lib/types";

function hasNewFeelBlueprint(content: CoachingContent): boolean {
  return Boolean(content.feel_blueprint?.strengths?.length && content.feel_blueprint.opening_narrative);
}

function hasCompactFeelBlueprint(content: CoachingContent): boolean {
  const fb = content.feel_blueprint;
  return Boolean(fb?.posture_check && fb?.real_culprit);
}

function hasLegacyDiagnostic(content: CoachingContent): boolean {
  return Boolean(content.diagnostic?.headline);
}

/** Parse coaching JSON from report (new or legacy). */
export function parseCoachingContent(report: SwingReport): CoachingContent | null {
  const stored = report.coaching_content;
  if (
    stored &&
    (hasNewFeelBlueprint(stored) || hasCompactFeelBlueprint(stored) || hasLegacyDiagnostic(stored)) &&
    stored.blueprint &&
    stored.roadmap
  ) {
    return stored;
  }
  const raw = report.gemini_raw as CoachingContent | null | undefined;
  if (
    raw &&
    (hasNewFeelBlueprint(raw) || hasCompactFeelBlueprint(raw) || hasLegacyDiagnostic(raw)) &&
    raw.blueprint &&
    raw.roadmap
  ) {
    return raw;
  }
  return null;
}

function compactToFull(fb: FeelBlueprintDiagnostic): FeelBlueprintDiagnostic {
  if (fb.strengths?.length) return fb;
  return {
    opening_narrative: fb.posture_check ?? "",
    headline: fb.headline,
    strengths: [
      {
        title: "What we saw at address",
        detail: fb.posture_check ?? "",
      },
      {
        title: "Prior progress",
        detail: "Building on your last session focus.",
      },
    ],
    flaws: [
      {
        title: "The real culprit",
        detail: fb.real_culprit ?? "",
      },
      {
        title: "Ball flight physics",
        detail: fb.kinetic_reaction ?? "",
      },
    ],
    current_ceiling: "See potential ceiling if they apply the pro fixes below.",
    potential_ceiling: "Fixing the root setup flaw should raise their consistent ceiling.",
    pro_fixes: [
      {
        title: "Primary feel",
        detail: fb.body_part_cue ?? "",
      },
      {
        title: "Spatial feel",
        detail: fb.spatial_cue ?? "",
      },
    ],
    body_part_cue: fb.body_part_cue ?? "",
    spatial_cue: fb.spatial_cue ?? "",
  };
}

export function getFeelBlueprint(content: CoachingContent): FeelBlueprintDiagnostic | null {
  if (content.feel_blueprint) {
    if (hasNewFeelBlueprint(content)) return content.feel_blueprint;
    if (hasCompactFeelBlueprint(content)) return compactToFull(content.feel_blueprint);
  }
  if (!content.diagnostic) return null;
  const d = content.diagnostic;
  const strengths: AnalysisBullet[] = [
    { title: "Committed to the shot", detail: "You're in the app working on your game." },
  ];
  const flaws: AnalysisBullet[] = [
    { title: d.headline, detail: d.mechanical_cause },
    { title: "Ball flight", detail: d.what_your_eye_sees },
  ];
  return {
    opening_narrative: d.mechanical_cause,
    headline: d.headline,
    strengths,
    flaws,
    current_ceiling: d.what_your_eye_sees,
    potential_ceiling: d.kinetic_chain,
    pro_fixes: [
      {
        title: "Range focus",
        detail: content.blueprint.steps[0]?.feel ?? "One feel at a time.",
      },
    ],
    body_part_cue: content.blueprint.steps[0]?.feel ?? "—",
    spatial_cue: d.kinetic_chain,
  };
}

export function isLegacyCoachingFormat(content: CoachingContent): boolean {
  return !hasNewFeelBlueprint(content) && !hasCompactFeelBlueprint(content) && Boolean(content.diagnostic);
}

export function getReportFocusLabel(report: SwingReport): string | null {
  const content = parseCoachingContent(report);
  if (content?.roadmap?.weekly_focus) {
    return content.roadmap.weekly_focus.replace(/\*\*/g, "");
  }
  const feel = content ? getFeelBlueprint(content) : null;
  if (feel?.headline) return feel.headline;
  return report.main_diagnosis;
}

function cleanText(value: unknown, fallback = "") {
  if (typeof value === "string") return value.replace(/\s+/g, " ").trim();
  return fallback;
}

function dedupe(items: Array<string | null | undefined>, limit: number) {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const item of items) {
    const cleaned = cleanText(item);
    if (!cleaned) continue;
    const key = cleaned.toLowerCase().replace(/[.]/g, "");
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(cleaned);
    if (result.length >= limit) break;
  }
  return result;
}

function label(text: string) {
  return text.replaceAll("_", " ");
}

function plainEvidence(diagnosis?: SwingDiagnosisEngine | null) {
  return (diagnosis?.evidence ?? []).slice(0, 4).map((item) => {
    const checkpoint = label(item.checkpoint);
    const metric = label(item.metric)
      .replace("trail elbow position", "trail arm position")
      .replace("club forearm plane proxy", "club and arm plane");
    return item.interpretation
      ? `At ${checkpoint}, ${metric} supported the diagnosis: ${item.interpretation}`
      : `At ${checkpoint}, ${metric} supported the diagnosis.`;
  });
}

function drillSteps(text: string) {
  const parts = text
    .split(".")
    .map((part) => part.trim())
    .filter(Boolean)
    .slice(0, 5);
  const fallback = [
    "Put a towel under your trail armpit",
    "Make slow three-quarter swings",
    "Keep the connection light until the top",
    "Hit easy shots before adding speed",
  ];
  while (parts.length < 3) parts.push(fallback[parts.length]);
  return parts.map((part) => (part.endsWith(".") ? part : `${part}.`));
}

export function getCoachSummaryReport(content: CoachingContent): CoachSummaryReport {
  if (content.coach_summary_report) return content.coach_summary_report;

  const feel = getFeelBlueprint(content);
  const diagnosis = content.diagnosis_engine;
  const improvement = content.improvement_engine;
  const practice = improvement?.practice_plan;
  const drill = practice?.primary_drill;
  const pga = content.pga_coach_analysis;

  const mainLeak = cleanText(
    improvement?.main_diagnosis || diagnosis?.main_diagnosis || feel?.flaws?.[0]?.detail,
    "There is one main swing leak to fix first."
  );
  const whyItMatters = cleanText(
    improvement?.expected_ball_flight_consequence || diagnosis?.chain_reaction,
    "It makes strike and direction depend too much on timing."
  );
  const feels = dedupe(
    [
      ...(practice?.feels ?? []),
      feel?.body_part_cue,
      feel?.spatial_cue,
      diagnosis?.what_to_feel,
    ],
    3
  );
  const whatsWorking = dedupe(
    [
      ...(feel?.strengths ?? []).map((item) => item.detail || item.title),
      pga?.pga_analysis,
    ],
    3
  );

  return {
    coach_summary: cleanText(
      pga?.pga_analysis || feel?.opening_narrative,
      `${mainLeak} ${whyItMatters}`
    ),
    whats_working: whatsWorking.length
      ? whatsWorking
      : ["There is at least one useful athletic pattern to build around."],
    main_swing_leak: mainLeak,
    why_it_matters: whyItMatters,
    feel_this_week: cleanText(
      practice?.practice_goal || feel?.body_part_cue || diagnosis?.what_to_feel,
      "Make the first fix simple enough to repeat."
    ),
    what_to_feel: feels.length ? feels : ["Keep the first fix simple and slow enough to feel."],
    fix_it_drill: {
      name: cleanText(drill?.name || diagnosis?.one_drill?.name, "Fix-It Drill"),
      steps: drillSteps(cleanText(drill?.how_to_do_it || diagnosis?.one_drill?.instructions)),
      dose: cleanText(practice?.dosage || diagnosis?.one_drill?.sets_reps, "15-20 balls at 60% speed."),
      success_check: cleanText(practice?.success_check || diagnosis?.one_drill?.success_metric, "You can repeat the feel without rushing."),
    },
    practice_plan_7_day: [
      "Day 1-2: rehearsal swings only.",
      "Day 3-4: 15-20 half-speed balls.",
      "Day 5-6: blend the feel into normal swings.",
      "Day 7: upload the recommended angle.",
    ],
    next_upload_goal: cleanText(
      improvement?.improvement_benchmark?.upload_instruction || pga?.next_upload_focus || diagnosis?.next_upload_focus || content.next_upload_focus,
      "Film the same swing from down-the-line and check the main checkpoint."
    ),
    advanced_details: {
      first_breakdown_checkpoint: cleanText(diagnosis?.first_breakdown_checkpoint, "unknown"),
      root_cause: cleanText(diagnosis?.root_cause, mainLeak),
      symptom: cleanText(diagnosis?.symptom, whyItMatters),
      confidence_note: cleanText(pga?.confidence_note || improvement?.confidence?.why, "Confidence depends on video angle and club visibility."),
      camera_angle_limitations: cleanText(diagnosis?.coach_warning, "A second camera angle may confirm path and face details."),
      evidence_plain_english: plainEvidence(diagnosis),
      raw_metrics: { evidence: diagnosis?.evidence ?? [] },
    },
  };
}
