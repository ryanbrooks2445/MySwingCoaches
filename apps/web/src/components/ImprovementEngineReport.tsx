"use client";

import { ReportMarkdown } from "@/components/ReportMarkdown";
import { Card } from "@/components/ui/Card";
import type { ImpactLevel, ImprovementEngine } from "@/lib/types";

interface ImprovementEngineReportProps {
  engine: ImprovementEngine;
}

function levelClass(level: ImpactLevel | string) {
  if (level === "high") return "text-red-500";
  if (level === "medium") return "text-amber-500";
  return "text-[var(--color-accent)]";
}

function scoreColor(score: number) {
  if (score >= 75) return "bg-[var(--color-accent)]";
  if (score >= 55) return "bg-amber-500";
  return "bg-red-500";
}

export function ImprovementEngineReport({ engine }: ImprovementEngineReportProps) {
  const progress = engine.progress_score;
  const value = engine.practice_value_score;

  return (
    <section className="mt-10">
      <p className="text-sm font-medium uppercase tracking-widest text-[var(--color-accent)]">
        Improvement engine
      </p>
      <h2 className="mt-1 text-2xl font-semibold">Your biggest shot leak</h2>

      <Card className="mt-4 space-y-8">
        <div>
          <h3 className="text-lg font-semibold">{engine.main_diagnosis}</h3>
          <ReportMarkdown
            content={engine.expected_ball_flight_consequence}
            className="mt-2 text-sm leading-relaxed"
          />
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-muted)]">
              Score impact
            </p>
            <p className={`mt-1 text-sm font-semibold capitalize ${levelClass(engine.estimated_score_impact.level)}`}>
              {engine.estimated_score_impact.level}
            </p>
            <ReportMarkdown
              content={`${engine.estimated_score_impact.shots_at_risk}\n\n${engine.estimated_score_impact.explanation}`}
              className="mt-2 text-sm leading-relaxed"
            />
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-muted)]">
              Confidence
            </p>
            <p className={`mt-1 text-sm font-semibold capitalize ${levelClass(engine.confidence.level)}`}>
              {engine.confidence.level}
            </p>
            <ReportMarkdown content={engine.confidence.why} className="mt-2 text-sm leading-relaxed" />
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-muted)]">
              Practice value
            </p>
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
              <span>Contact: <strong className={levelClass(value.contact)}>{value.contact}</strong></span>
              <span>Direction: <strong className={levelClass(value.direction)}>{value.direction}</strong></span>
              <span>Consistency: <strong className={levelClass(value.consistency)}>{value.consistency}</strong></span>
              <span>Distance: <strong className={levelClass(value.distance)}>{value.distance}</strong></span>
            </div>
            <ReportMarkdown content={value.summary} className="mt-2 text-sm leading-relaxed" />
          </div>
        </div>

        <div className="grid gap-5 md:grid-cols-2">
          <div>
            <h3 className="text-base font-semibold">Fix this first</h3>
            <ReportMarkdown content={engine.fix_priority.fix_first} className="mt-2 text-sm leading-relaxed" />
            <p className="mt-4 text-xs font-medium uppercase tracking-wide text-[var(--color-muted)]">
              Second, only after that improves
            </p>
            <ReportMarkdown content={engine.fix_priority.fix_second} className="mt-2 text-sm leading-relaxed" />
            <ReportMarkdown content={engine.fix_priority.why_this_order} className="mt-3 text-sm leading-relaxed" />
          </div>

          <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4">
            <h3 className="text-base font-semibold text-amber-700 dark:text-amber-400">
              What you should ignore right now
            </h3>
            <ul className="mt-3 space-y-2 text-sm">
              {engine.fix_priority.ignore_for_now.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </div>

        <div>
          <h3 className="text-base font-semibold">Practice tomorrow</h3>
          <p className="mt-1 text-sm font-medium text-[var(--color-accent)]">
            {engine.practice_plan.practice_goal}
          </p>
          <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm">
            {engine.practice_plan.tomorrow_plan.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>

          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-muted)]">
                Primary drill
              </p>
              <p className="mt-1 font-medium">{engine.practice_plan.primary_drill.name}</p>
              <ReportMarkdown
                content={`${engine.practice_plan.primary_drill.why_it_helps}\n\n${engine.practice_plan.primary_drill.how_to_do_it}`}
                className="mt-2 text-sm leading-relaxed"
              />
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-muted)]">
                Dose and success check
              </p>
              <ReportMarkdown
                content={`${engine.practice_plan.dosage}\n\n${engine.practice_plan.success_check}`}
                className="mt-2 text-sm leading-relaxed"
              />
              <div className="mt-3 flex flex-wrap gap-2">
                {engine.practice_plan.feels.map((feel) => (
                  <span key={feel} className="rounded-full bg-[var(--color-border)]/60 px-3 py-1 text-xs">
                    {feel}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-[var(--color-accent)]/30 bg-[var(--color-accent)]/10 p-4">
          <h3 className="text-base font-semibold text-[var(--color-accent)]">Next upload benchmark</h3>
          <p className="mt-2 text-sm font-medium">{engine.improvement_benchmark.metric}</p>
          <ReportMarkdown
            content={`${engine.improvement_benchmark.current_state}\n\n${engine.improvement_benchmark.target_next_upload}\n\n${engine.improvement_benchmark.upload_instruction}`}
            className="mt-2 text-sm leading-relaxed"
          />
        </div>

        <div>
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h3 className="text-base font-semibold">Progress score</h3>
              <ReportMarkdown content={progress.summary} className="mt-1 text-sm leading-relaxed" />
            </div>
            <div className="text-right">
              <p className="text-3xl font-semibold">{progress.overall}</p>
              {progress.previous_overall !== null && progress.previous_overall !== undefined && (
                <p className="text-xs text-[var(--color-muted)]">
                  Previous {progress.previous_overall}
                </p>
              )}
            </div>
          </div>
          <div className="mt-4 space-y-3">
            {progress.metrics.map((metric) => (
              <div key={metric.name}>
                <div className="flex items-center justify-between gap-3 text-sm">
                  <span className="font-medium">{metric.name}</span>
                  <span className="text-[var(--color-muted)]">
                    {metric.previous_score !== null && metric.previous_score !== undefined
                      ? `${metric.previous_score} → ${metric.current_score}`
                      : metric.current_score}
                  </span>
                </div>
                <div className="mt-1 h-2 overflow-hidden rounded-full bg-[var(--color-border)]">
                  <div
                    className={`h-full ${scoreColor(metric.current_score)}`}
                    style={{ width: `${metric.current_score}%` }}
                  />
                </div>
                <p className="mt-1 text-xs text-[var(--color-muted)]">{metric.interpretation}</p>
              </div>
            ))}
          </div>
        </div>
      </Card>
    </section>
  );
}
