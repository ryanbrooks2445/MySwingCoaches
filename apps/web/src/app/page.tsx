import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { PRICE_PER_ANALYSIS_DISPLAY } from "@/lib/pricing";
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
            Player Improvement Engine
          </p>
          <h1 className="mx-auto max-w-3xl text-4xl font-semibold tracking-tight md:text-6xl">
            Golf Swing Analysis You Can Take to the Range
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-[var(--color-muted)]">
            Upload a full swing, chip, or putt for {PRICE_PER_ANALYSIS_DISPLAY}. Get a clear diagnosis, one main fix, practical feels, and a 7-day practice plan.
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
            <p className="mb-2 text-sm text-[var(--color-muted)]">Upload</p>
            <div className="flex aspect-video items-center justify-center rounded-xl border-2 border-dashed border-[var(--color-border)] bg-[var(--color-background)]">
              <div className="text-center">
                <p className="font-medium">Drop your swing video</p>
                <p className="text-sm text-[var(--color-muted)]">MP4 · MOV · from your phone</p>
              </div>
            </div>
          </Card>

          <Card className="space-y-4 text-left">
            <p className="text-sm text-[var(--color-muted)]">Sample Analysis Preview</p>
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
              { title: "Clear Diagnosis", desc: "Ball flight tied to swing mechanics, with the compensation explained in plain English." },
              { title: "Practice-Ready Feels", desc: "Setup anchors, visual cues, and constraint drills focused on one priority at a time." },
              { title: "7-Day Practice Plan", desc: "A simple weekly plan with a clear Day 7 check before your next upload." },
              { title: "No Fake Precision", desc: "No gimmicky swing scores. Just practical coaching you can use over the ball." },
              { title: "Private Video Handling", desc: "Your upload is stored privately and signed only when the app needs to analyze or display it." },
              { title: "Reference Frames", desc: "Key moments from your swing alongside your analysis." },
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
            <Button size="lg">Analyze my swing</Button>
          </Link>
        </section>
      </main>
    </div>
  );
}
