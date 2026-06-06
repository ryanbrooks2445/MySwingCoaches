import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { PRICE_FIRST_ANALYSIS_DISPLAY, PRICE_PER_ANALYSIS_DISPLAY } from "@/lib/pricing";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/StatusBadge";

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-6">
        <span className="text-lg font-semibold">MySwingCoaches</span>
        <div className="flex gap-3">
          <Link href="/login">
            <Button variant="ghost">Log in</Button>
          </Link>
          <Link href="/signup">
            <Button>Get started</Button>
          </Link>
        </div>
      </header>

      <main>
        <section className="mx-auto max-w-6xl px-4 py-20 text-center">
          <p className="mb-4 text-sm font-medium uppercase tracking-widest text-[var(--color-accent)]">
            Player-improvement engine
          </p>
          <h1 className="mx-auto max-w-3xl text-4xl font-semibold tracking-tight md:text-6xl">
            Not a report card. A coaching blueprint you can feel on the range.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-[var(--color-muted)]">
            Upload full swing, chipping, or putting — {PRICE_FIRST_ANALYSIS_DISPLAY} first swing, then{" "}
            {PRICE_PER_ANALYSIS_DISPLAY} each. Short blueprint, feels, and a 7-day plan.
          </p>
          <div className="mt-10 flex justify-center gap-4">
            <Link href="/signup">
              <Button size="lg">Build my blueprint</Button>
            </Link>
            <Link href="/pricing">
              <Button size="lg" variant="secondary">View pricing</Button>
            </Link>
          </div>
        </section>

        <section className="mx-auto grid max-w-6xl gap-8 px-4 pb-24 md:grid-cols-2">
          <Card>
            <p className="mb-2 text-sm text-[var(--color-muted)]">Upload</p>
            <div className="flex aspect-video items-center justify-center rounded-xl border-2 border-dashed border-[var(--color-border)] bg-[var(--color-background)]">
              <div className="text-center">
                <p className="font-medium">Drop your swing video</p>
                <p className="text-sm text-[var(--color-muted)]">MP4 · MOV · from your phone</p>
              </div>
            </div>
          </Card>

          <Card className="space-y-4 text-left">
            <p className="text-sm text-[var(--color-muted)]">Sample blueprint preview</p>
            <StatusBadge status="current_focus" />
            <p className="text-lg font-semibold">The Over-the-Top Cut</p>
            <p className="text-sm text-[var(--color-muted)]">
              <strong className="text-[var(--color-foreground)]">The feel:</strong> Turn your shirt buttons to the target before you swing down.
            </p>
            <p className="text-sm text-[var(--color-muted)]">
              <strong className="text-[var(--color-foreground)]">This week:</strong> Rotation — Day 1–3 living-room turns, no club.
            </p>
          </Card>
        </section>

        <section className="border-t border-[var(--color-border)] bg-[var(--color-card)] py-20">
          <div className="mx-auto grid max-w-6xl gap-6 px-4 md:grid-cols-3">
            {[
              { title: "Diagnostic truth", desc: "Ball flight tied to physics — why your body chose the compensation." },
              { title: "Kinesthetic blueprint", desc: "Setup anchors, visual cues, and constraint drills — one feel at a time." },
              { title: "7-day milestones", desc: "Unlock phases as you lock in the feel. Clear Day 7 test before your next upload." },
              { title: "No score gimmicks", desc: "Zero report-card numbers. Actionable feels you can use standing over the ball." },
              { title: "Optional coach review", desc: "Add human review from a coach (stub — coming with Stripe integration)." },
              { title: "Video reference frames", desc: "Key moments from your swing alongside the blueprint." },
            ].map((f) => (
              <Card key={f.title}>
                <h3 className="font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm text-[var(--color-muted)]">{f.desc}</p>
              </Card>
            ))}
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-4 py-20 text-center">
          <h2 className="text-3xl font-semibold">Ready to train with purpose?</h2>
          <Link href="/signup" className="mt-6 inline-block">
            <Button size="lg">Get started — {PRICE_FIRST_ANALYSIS_DISPLAY}</Button>
          </Link>
        </section>
      </main>
    </div>
  );
}
