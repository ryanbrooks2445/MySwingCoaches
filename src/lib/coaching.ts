import type {
  CoachingContent,
  FeelBlueprintDiagnostic,
  SimplifiedSwingReport,
  SwingDiagnosisEngine,
  SwingReport,
} from "@/lib/types";
import { parseCoachVerdictFromAnalysis, resolveCoachVerdict } from "@/lib/coach-verdict";

function hasSimplifiedReport(content: CoachingContent): boolean {
  return Boolean(content.pga_analysis?.trim() && content.main_fix?.trim());
}

function hasNewFeelBlueprint(content: CoachingContent): boolean {
  return Boolean(content.feel_blueprint?.strengths?.length && content.feel_blueprint.opening_narrative);
}

function hasLegacyDiagnostic(content: CoachingContent): boolean {
  return Boolean(content.diagnostic?.headline);
}

function hasDiagnosisEngine(content: CoachingContent): boolean {
  return Boolean(content.diagnosis_engine?.main_diagnosis);
}

/** Parse coaching JSON from report. */
export function parseCoachingContent(report: SwingReport): CoachingContent | null {
  const tryParse = (raw: CoachingContent | null | undefined): CoachingContent | null => {
    if (!raw) return null;
    if (hasSimplifiedReport(raw)) return raw;
    if (hasDiagnosisEngine(raw) || hasNewFeelBlueprint(raw) || hasLegacyDiagnostic(raw)) {
      return raw;
    }
    if (raw.blueprint && raw.roadmap) return raw;
    return null;
  };

  return tryParse(report.coaching_content) ?? tryParse(report.gemini_raw as unknown as CoachingContent);
}

function diagnosisToSimplified(d: SwingDiagnosisEngine, content: CoachingContent): SimplifiedSwingReport {
  const tips = d.what_to_feel
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 8)
    .slice(0, 4);
  if (tips.length === 0 && d.what_to_feel) tips.push(d.what_to_feel);

  const drills = d.one_drill?.name
    ? [
        {
          name: d.one_drill.name,
          why_it_helps: d.one_drill.success_metric,
          how_to_do_it: d.one_drill.instructions,
        },
      ]
    : [];

  return {
    pga_analysis: [d.main_diagnosis, d.skill_level_note].filter(Boolean).join(" "),
    main_fix: d.fix_priority.primary,
    tips_and_feels: tips,
    drills,
    next_swing_check: d.next_upload_focus || content.next_upload_focus,
    advanced_details: {
      root_cause: d.root_cause,
      symptom: d.symptom,
      evidence_metrics: d.evidence?.map((e) => `${e.metric}: ${e.observed}`) ?? [],
      secondary_fix: d.fix_priority.secondary,
      optional_fix: d.fix_priority.optional,
      chain_reaction: d.chain_reaction,
      why_it_caused_the_miss: d.symptom,
      confidence_score: 0.8,
      next_checkpoint: d.first_breakdown_checkpoint,
    },
  };
}

function feelBlueprintToSimplified(content: CoachingContent, fb: FeelBlueprintDiagnostic): SimplifiedSwingReport {
  const primaryFix = fb.pro_fixes[0];
  const tips = [
    fb.body_part_cue,
    fb.spatial_cue,
    ...fb.pro_fixes.slice(1).map((p) => `${p.title}: ${p.detail}`),
  ].filter(Boolean);

  const drills = fb.pro_fixes.slice(0, 3).map((p) => ({
    name: p.title,
    why_it_helps: p.detail,
    how_to_do_it: "15–20 reps at half speed before full swings.",
  }));

  if (drills.length === 0 && content.blueprint?.steps?.length) {
    for (const step of content.blueprint.steps.slice(0, 3)) {
      drills.push({
        name: step.title,
        why_it_helps: step.adjustment ?? step.action ?? step.feel,
        how_to_do_it: step.success_condition ?? step.feel,
      });
    }
  }

  const strengthsBlock = fb.strengths
    .map((s) => `${s.title}: ${s.detail}`)
    .join(" ");
  const missingBlock = fb.flaws.map((f) => `${f.title}: ${f.detail}`).join(" ");
  const unlockBlock = fb.potential_ceiling?.trim()
    ? `What changes when you unlock it\n\n${fb.potential_ceiling}`
    : "";
  return {
    pga_analysis: [
      "What's working",
      strengthsBlock || fb.opening_narrative,
      "The missing piece",
      missingBlock || fb.opening_narrative,
      unlockBlock,
    ]
      .filter(Boolean)
      .join("\n\n"),
    main_fix: primaryFix ? `${primaryFix.title}: ${primaryFix.detail}` : fb.body_part_cue,
    tips_and_feels: tips.slice(0, 4),
    drills: drills.slice(0, 3),
    next_swing_check: content.next_swing_check ?? content.next_upload_focus,
    advanced_details: {
      root_cause: fb.flaws[0]?.detail ?? "",
      symptom: fb.flaws[1]?.detail ?? "",
      evidence_metrics: fb.flaws.map((f) => f.title),
      secondary_fix: fb.pro_fixes[1]?.detail ?? "",
      optional_fix: fb.pro_fixes[2]?.detail ?? "",
      chain_reaction: fb.flaws.map((f) => f.title).join(" → "),
      why_it_caused_the_miss: fb.current_ceiling,
      confidence_score: 0.75,
      next_checkpoint: content.blueprint?.steps[0]?.title ?? "",
    },
  };
}

export function getSimplifiedReport(content: CoachingContent): SimplifiedSwingReport {
  if (hasSimplifiedReport(content)) {
    const simplified: SimplifiedSwingReport = {
      pga_analysis: content.pga_analysis!,
      main_fix: content.main_fix!,
      tips_and_feels: content.tips_and_feels ?? [],
      drills: content.drills ?? [],
      practice_plan: content.roadmap?.milestones?.map(
        (milestone) => `${milestone.days}: ${milestone.detail}`
      ),
      next_swing_check: content.next_swing_check ?? content.next_upload_focus,
      advanced_details: content.advanced_details ?? {
        report_mode: "development",
        foundational_missing_piece: "",
        root_cause: "",
        symptom: "",
        evidence_metrics: [],
        secondary_fix: "",
        optional_fix: "",
        chain_reaction: "",
        why_it_caused_the_miss: "",
        confidence_score: 0,
      },
      coach_verdict:
        resolveCoachVerdict(content, {
          pga_analysis: content.pga_analysis,
          main_fix: content.main_fix,
        }) ?? undefined,
    };
    return simplified;
  }
  if (content.diagnosis_engine) {
    return diagnosisToSimplified(content.diagnosis_engine, content);
  }
  if (content.feel_blueprint && hasNewFeelBlueprint(content)) {
    const simplified = feelBlueprintToSimplified(content, content.feel_blueprint);
    simplified.coach_verdict =
      resolveCoachVerdict(content, simplified) ??
      parseCoachVerdictFromAnalysis(simplified.pga_analysis, {
        biggest_positive: content.feel_blueprint.strengths[0]?.detail,
        main_issue: content.feel_blueprint.flaws[0]?.detail,
        best_fix: content.feel_blueprint.pro_fixes[0]?.detail,
      }) ??
      undefined;
    return simplified;
  }
  if (content.diagnostic && content.blueprint) {
    const d = content.diagnostic;
    return {
      pga_analysis: `${d.headline}. ${d.mechanical_cause}`,
      main_fix: d.mechanical_cause,
      tips_and_feels: [content.blueprint.steps[0]?.feel ?? d.mechanical_cause],
      drills: content.blueprint.steps.slice(0, 3).map((s) => ({
        name: s.title,
        why_it_helps: s.adjustment ?? s.feel,
        how_to_do_it: s.success_condition ?? s.feel,
      })),
      next_swing_check: content.next_upload_focus,
      advanced_details: {
        root_cause: d.mechanical_cause,
        symptom: d.what_your_eye_sees,
        evidence_metrics: [],
        secondary_fix: "",
        optional_fix: "",
        chain_reaction: d.kinetic_chain,
        why_it_caused_the_miss: d.what_your_eye_sees,
        confidence_score: 0.7,
      },
    };
  }
  return {
    pga_analysis: "Upload a new swing for your coach plan.",
    main_fix: "—",
    tips_and_feels: [],
    drills: [],
    next_swing_check: content.next_upload_focus,
    advanced_details: {
      root_cause: "",
      symptom: "",
      evidence_metrics: [],
      secondary_fix: "",
      optional_fix: "",
      chain_reaction: "",
      why_it_caused_the_miss: "",
      confidence_score: 0,
    },
  };
}

/** @deprecated Use getSimplifiedReport */
export function getFeelBlueprint(content: CoachingContent): FeelBlueprintDiagnostic | null {
  return content.feel_blueprint ?? null;
}

export function getReportFocusLabel(report: SwingReport): string | null {
  const content = parseCoachingContent(report);
  if (!content) return report.main_diagnosis;
  const simple = getSimplifiedReport(content);
  return simple.pga_analysis.split(/[.!?]/)[0]?.trim() || report.main_diagnosis;
}
