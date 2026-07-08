import Link from "next/link";
import { CheckCircle2, Lock, RotateCcw, Video } from "lucide-react";
import { PublicHeader } from "@/components/PublicHeader";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { PRICE_PER_ANALYSIS_DISPLAY } from "@/lib/pricing";

const deliverables = [
  "One swing priority, not a list of ten fixes",
  "Evidence from visible checkpoints in your video",
  "One feel and one matched practice drill",
  "A seven-day practice plan and next-upload goal",
];

const faqs = [
  ["How long does it take?", "Most reports are ready in 2–5 minutes. Free-tier cold starts can occasionally take longer."],
  ["What should I film?", "Use face-on or down-the-line. Keep your full body, club, and ball area visible in good light."],
  ["What if analysis fails?", "We retry automatically. If a report still cannot be completed, your analysis credit is restored."],
  ["Are my videos public?", "No. Videos use private storage and short-lived signed links, then are removed after 30 days."],
  ["Is this a PGA lesson?", "No. It is AI-assisted coaching guidance and does not replace an in-person certified golf professional."],
];

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <PublicHeader />
      <main>
        <section className="border-b border-[var(--color-border)]">
          <div className="mx-auto max-w-6xl px-4 py-14 text-center sm:py-20">
            <p className="text-sm font-semibold uppercase text-[var(--color-accent)]">
              AI golf swing analysis
            </p>
            <h1 className="mx-auto mt-4 max-w-4xl text-4xl font-semibold leading-tight sm:text-6xl">
              Upload one swing. Know exactly what to practice next.
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-[var(--color-muted)]">
              Get one priority, evidence from your video, a feel, a drill, and a clear next-upload
              goal. {PRICE_PER_ANALYSIS_DISPLAY} per swing analysis.
            </p>
            <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
              <Link href="/signup?redirect=/upload">
                <Button size="lg" className="w-full sm:w-auto">Analyze my swing</Button>
              </Link>
              <Link href="/pricing">
                <Button size="lg" variant="secondary" className="w-full sm:w-auto">See pricing</Button>
              </Link>
              <Link href="/example">
                <Button size="lg" variant="secondary" className="w-full sm:w-auto">See example report</Button>
              </Link>
            </div>
            <p className="mt-4 text-sm text-[var(--color-muted)]">
              Private upload · 30-day video retention · failed-analysis credit guarantee
            </p>
          </div>
        </section>

        <section className="mx-auto grid max-w-6xl gap-10 px-4 py-16 lg:grid-cols-[0.9fr_1.1fr]">
          <div>
            <p className="text-sm font-semibold text-[var(--color-accent)]">What you receive</p>
            <h2 className="mt-2 text-3xl font-semibold">A coach-style plan you can use at the range</h2>
            <ul className="mt-6 space-y-4">
              {deliverables.map((item) => (
                <li key={item} className="flex gap-3 text-[var(--color-muted)]">
                  <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-[var(--color-accent)]" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
          <Card className="rounded-lg border-[var(--color-accent)]/30">
            <p className="text-xs font-semibold uppercase text-[var(--color-accent)]">
              Anonymized real report example
            </p>
            <h3 className="mt-3 text-xl font-semibold">Main priority: athletic setup balance</h3>
            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              <div>
                <p className="text-xs font-semibold uppercase text-[var(--color-muted)]">Evidence</p>
                <p className="mt-1 text-sm leading-relaxed text-[var(--color-muted)]">
                  Pressure began too far toward the heels, forcing the body toward the ball later.
                </p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase text-[var(--color-muted)]">Feel</p>
                <p className="mt-1 text-sm leading-relaxed text-[var(--color-muted)]">
                  Feel pressure under your laces before the takeaway.
                </p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase text-[var(--color-muted)]">Drill</p>
                <p className="mt-1 text-sm leading-relaxed text-[var(--color-muted)]">
                  Ten athletic setup rehearsals, then fifteen half-speed shots.
                </p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase text-[var(--color-muted)]">Next upload</p>
                <p className="mt-1 text-sm leading-relaxed text-[var(--color-muted)]">
                  Confirm centered pressure and stable posture from face-on.
                </p>
              </div>
            </div>
            <Link href="/example" className="mt-5 inline-flex text-sm font-medium text-[var(--color-accent)] hover:underline">
              View full example report →
            </Link>
          </Card>
        </section>

        <section className="border-y border-[var(--color-border)] bg-[var(--color-card)]">
          <div className="mx-auto max-w-6xl px-4 py-16">
            <h2 className="text-center text-3xl font-semibold">From visible problem to practice goal</h2>
            <div className="mt-10 grid gap-6 md:grid-cols-3">
              {[
                ["1. We inspect", "Setup, backswing structure, transition, impact, and finish are checked in order."],
                ["2. We prioritize", "The report chooses the earliest visible issue instead of repeating generic swing tips."],
                ["3. You train", "One feel and drill lead to a specific checkpoint for your next video."],
              ].map(([title, body]) => (
                <div key={title} className="border-l-2 border-[var(--color-accent)] pl-4">
                  <h3 className="font-semibold">{title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-[var(--color-muted)]">{body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-4 py-16">
          <div className="grid gap-6 sm:grid-cols-3">
            {[
              [Lock, "Private by default", "Videos are stored privately and accessed with short-lived signed links."],
              [RotateCcw, "Failure guarantee", "If automatic retries cannot finish your report, your credit is restored."],
              [Video, "Built for phone video", "Upload MP4 or MOV clips up to 100 MB and 30 seconds."],
            ].map(([Icon, title, body]) => {
              const IconComponent = Icon as typeof Lock;
              return (
                <div key={String(title)} className="rounded-lg border border-[var(--color-border)] p-5">
                  <IconComponent className="h-5 w-5 text-[var(--color-accent)]" />
                  <h3 className="mt-4 font-semibold">{String(title)}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-[var(--color-muted)]">{String(body)}</p>
                </div>
              );
            })}
          </div>
        </section>

        <section className="border-t border-[var(--color-border)] bg-[var(--color-card)]">
          <div className="mx-auto max-w-3xl px-4 py-16">
            <h2 className="text-center text-3xl font-semibold">Questions golfers ask first</h2>
            <div className="mt-8 divide-y divide-[var(--color-border)] border-y border-[var(--color-border)]">
              {faqs.map(([question, answer]) => (
                <details key={question} className="py-4">
                  <summary className="cursor-pointer font-medium">{question}</summary>
                  <p className="mt-3 text-sm leading-relaxed text-[var(--color-muted)]">{answer}</p>
                </details>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-4 py-16 text-center">
          <h2 className="text-3xl font-semibold">Give your next range session one clear purpose.</h2>
          <Link href="/signup?redirect=/upload" className="mt-6 inline-block">
            <Button size="lg">Get my analysis — {PRICE_PER_ANALYSIS_DISPLAY}</Button>
          </Link>
        </section>
      </main>
    </div>
  );
}
