import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ScoreBar } from "@/components/ScoreRing";

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
            AI-powered swing analysis
          </p>
          <h1 className="mx-auto max-w-3xl text-4xl font-semibold tracking-tight md:text-6xl">
            Upload your swing. Get a coach-level breakdown in minutes.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-[var(--color-muted)]">
            Pose tracking, swing metrics, and Gemini-powered coaching — built for golfers who want
            structured feedback without waiting for a lesson.
          </p>
          <div className="mt-10 flex justify-center gap-4">
            <Link href="/signup">
              <Button size="lg">Analyze my swing</Button>
            </Link>
            <Link href="/pricing">
              <Button size="lg" variant="secondary">View pricing</Button>
            </Link>
          </div>
        </section>

        <section className="mx-auto grid max-w-6xl gap-8 px-4 pb-24 md:grid-cols-2">
          <Card>
            <p className="mb-2 text-sm text-[var(--color-muted)]">Upload mockup</p>
            <div className="flex aspect-video items-center justify-center rounded-xl border-2 border-dashed border-[var(--color-border)] bg-[var(--color-background)]">
              <div className="text-center">
                <p className="font-medium">Drop your swing video</p>
                <p className="text-sm text-[var(--color-muted)]">MP4 · MOV · from your phone</p>
              </div>
            </div>
          </Card>

          <Card className="space-y-6">
            <div>
              <p className="text-sm text-[var(--color-muted)]">AI swing score</p>
              <p className="text-5xl font-semibold text-[var(--color-accent)]">78</p>
              <p className="text-sm text-[var(--color-muted)]">Sample report preview</p>
            </div>
            <ScoreBar label="Setup" score={82} />
            <ScoreBar label="Backswing" score={75} />
            <ScoreBar label="Downswing" score={71} />
            <ScoreBar label="Impact" score={79} />
            <ScoreBar label="Finish" score={84} />
          </Card>
        </section>

        <section className="border-t border-[var(--color-border)] bg-[var(--color-card)] py-20">
          <div className="mx-auto grid max-w-6xl gap-6 px-4 md:grid-cols-3">
            {[
              { title: "Side-by-side correction", desc: "Compare your checkpoints to reference models (placeholder library today)." },
              { title: "Drill recommendations", desc: "Targeted practice plans based on detected swing issues." },
              { title: "Progress tracking", desc: "Score trends over time as you upload new swings." },
              { title: "Optional coach review", desc: "Add human review from a coach (stub — coming with Stripe integration)." },
              { title: "Pose-based metrics", desc: "MediaPipe landmarks drive objective measurements, not guesswork." },
              { title: "Gemini coaching report", desc: "AI narrative built from structured swing data and rules engine output." },
            ].map((f) => (
              <Card key={f.title}>
                <h3 className="font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm text-[var(--color-muted)]">{f.desc}</p>
              </Card>
            ))}
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-4 py-20 text-center">
          <h2 className="text-3xl font-semibold">Ready to improve your swing?</h2>
          <Link href="/signup" className="mt-6 inline-block">
            <Button size="lg">Start free analysis</Button>
          </Link>
        </section>
      </main>
    </div>
  );
}
