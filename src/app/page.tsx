import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  Clock,
  Eye,
  Gauge,
  ListOrdered,
  Lock,
  PlayCircle,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
  Video,
  Zap,
} from "lucide-react";
import { PublicHeader } from "@/components/PublicHeader";
import { Button } from "@/components/ui/Button";
import { Reveal } from "@/components/Reveal";
import { AnimatedStat } from "@/components/AnimatedStat";
import {
  PRICE_ANNUAL_UNLIMITED_DISPLAY,
  PRICE_PER_ANALYSIS_DISPLAY,
} from "@/lib/pricing";

const marqueeItems = [
  "Setup",
  "Takeaway",
  "Transition",
  "Impact",
  "Finish",
  "Fixes in priority order",
  "Evidence from film",
  "Steps for every fix",
  "Come back anytime",
];

const deliverables: {
  icon: typeof Target;
  title: string;
  body: string;
  span: string;
  glow: string;
}[] = [
  {
    icon: ListOrdered,
    title: "Fixes in priority order",
    body: "We read your swing and rank what's actually holding it back — root cause first — so you work on what moves the needle most, in the right sequence. Not a random pile of tips.",
    span: "sm:col-span-2",
    glow: "from-[var(--color-emerald)]/25",
  },
  {
    icon: Eye,
    title: "Evidence from your video",
    body: "Every fix is tied to a visible checkpoint in your own swing, setup through finish.",
    span: "",
    glow: "from-[var(--color-amber)]/25",
  },
  {
    icon: Zap,
    title: "Steps to fix each one",
    body: "Every fix comes with a feel and a range-ready drill you can actually do — clear steps, not vague advice.",
    span: "",
    glow: "from-[var(--color-lime)]/25",
  },
  {
    icon: TrendingUp,
    title: "Built around your swing",
    body: "Every golfer is different — some swings need a single change, others need several, and we show you all of them in order. If a fix gives you trouble, send a fresh swing anytime and we'll pick up right where you left off.",
    span: "sm:col-span-2",
    glow: "from-[var(--color-emerald)]/25",
  },
];

const steps: { icon: typeof Eye; step: string; title: string; body: string }[] = [
  {
    icon: Eye,
    step: "01",
    title: "We inspect",
    body: "Setup, takeaway, transition, impact, and finish are read in order, frame by frame.",
  },
  {
    icon: Target,
    step: "02",
    title: "We prioritize",
    body: "We rank every fix your swing needs — however many that is — starting with the root cause, so your effort compounds instead of scattering.",
  },
  {
    icon: CheckCircle2,
    step: "03",
    title: "You train",
    body: "Each fix comes with a feel, a drill, and a checkpoint. Struggling with one? Send another swing and we'll build on it.",
  },
];

const trustPoints: { icon: typeof Lock; title: string; body: string }[] = [
  {
    icon: Lock,
    title: "Private by default",
    body: "Videos use private storage and short-lived signed links, then are removed after 30 days.",
  },
  {
    icon: RotateCcw,
    title: "Failure guarantee",
    body: "If automatic retries can't finish your report, your analysis credit is restored — no questions.",
  },
  {
    icon: Video,
    title: "Built for phone video",
    body: "Upload an MP4 or MOV clip up to 100 MB and 30 seconds. No special equipment.",
  },
];

const faqs = [
  ["How long does it take?", "Most reports are ready in 2–5 minutes. Occasionally a cold start can take a little longer."],
  ["What should I film?", "Face-on or down-the-line, with your full body, club, and ball area visible in good light."],
  ["What if analysis fails?", "We retry automatically. If a report still can't be completed, your analysis credit is restored."],
  ["Are my videos public?", "No. Videos use private storage and short-lived signed links, then are removed after 30 days."],
  ["Is this a PGA lesson?", "No. It is AI-assisted coaching guidance and does not replace an in-person certified golf professional."],
];

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <PublicHeader />
      <main>
        {/* ── Hero ───────────────────────────────────────────── */}
        <section className="relative overflow-hidden bg-[var(--color-ink)] text-white">
          {/* animated ambient glow */}
          <div aria-hidden className="pointer-events-none absolute inset-0">
            <div
              className="blob absolute -left-24 -top-24 h-96 w-96 animate-drift"
              style={{ background: "radial-gradient(circle, rgba(16,185,129,0.55), transparent 70%)" }}
            />
            <div
              className="blob absolute -right-20 top-10 h-[26rem] w-[26rem] animate-float-slow"
              style={{ background: "radial-gradient(circle, rgba(245,158,11,0.35), transparent 70%)" }}
            />
            <div
              className="blob absolute bottom-[-6rem] left-1/3 h-80 w-80 animate-float"
              style={{ background: "radial-gradient(circle, rgba(74,222,128,0.4), transparent 70%)" }}
            />
            <div
              className="absolute inset-0 opacity-[0.06]"
              style={{
                backgroundImage:
                  "linear-gradient(rgba(255,255,255,.6) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.6) 1px, transparent 1px)",
                backgroundSize: "56px 56px",
              }}
            />
          </div>

          <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-4 py-20 sm:py-28 lg:grid-cols-[1.05fr_0.95fr]">
            <div>
              <Reveal
                as="p"
                className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-4 py-1.5 text-xs font-medium uppercase tracking-widest text-[var(--color-lime)] backdrop-blur"
              >
                <Sparkles className="h-3.5 w-3.5" />
                Evidence-based AI swing analysis
              </Reveal>

              <Reveal as="h1" delay={80} className="mt-7 font-display text-5xl font-bold leading-[1.02] tracking-tight sm:text-6xl lg:text-7xl">
                Stop guessing.
                <br />
                Know <span className="text-gradient">exactly</span> what
                <br />
                to practice next.
              </Reveal>

              <Reveal as="p" delay={160} className="mt-6 max-w-xl text-lg leading-relaxed text-white/70">
                Upload one swing. We read it frame by frame and hand you a prioritized fix list —
                what to work on first, the evidence from your own video, and clear steps for every
                fix. The way a real coach would break it down. In minutes.
              </Reveal>

              <Reveal delay={220} className="mt-9 flex flex-col gap-3 sm:flex-row sm:items-center">
                <Link href="/signup?redirect=/upload">
                  <Button
                    size="lg"
                    className="group w-full animate-pulse-glow rounded-full bg-gradient-to-r from-[var(--color-emerald)] to-[var(--color-lime)] text-[var(--color-ink)] hover:opacity-100 sm:w-auto"
                  >
                    Analyze my swing
                    <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                  </Button>
                </Link>
                <Link href="/example">
                  <Button
                    size="lg"
                    variant="secondary"
                    className="w-full rounded-full border-white/20 bg-white/5 text-white hover:bg-white/10 sm:w-auto"
                  >
                    <PlayCircle className="mr-2 h-4 w-4" />
                    See a real report
                  </Button>
                </Link>
              </Reveal>

              <Reveal delay={280} className="mt-6 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-white/60">
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-[var(--color-lime)]" />
                  {PRICE_PER_ANALYSIS_DISPLAY} per swing
                </span>
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-[var(--color-lime)]" />
                  {PRICE_ANNUAL_UNLIMITED_DISPLAY}/yr unlimited
                </span>
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-[var(--color-lime)]" />
                  Cancel anytime
                </span>
              </Reveal>
            </div>

            {/* Floating live-report mockup */}
            <Reveal delay={200} className="relative">
              <div className="animate-float ring-gradient rounded-3xl bg-[var(--color-ink-2)]/80 p-5 shadow-2xl backdrop-blur">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-[var(--color-lime)]">
                    <span className="relative flex h-2 w-2">
                      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[var(--color-lime)] opacity-75" />
                      <span className="relative inline-flex h-2 w-2 rounded-full bg-[var(--color-lime)]" />
                    </span>
                    Report ready
                  </span>
                  <span className="text-xs text-white/50">2m 41s</span>
                </div>

                <p className="mt-5 text-xs font-semibold uppercase tracking-wide text-white/50">
                  Fix 1 of 3 · in priority order
                </p>
                <h3 className="mt-1 font-display text-2xl font-semibold text-white">
                  Hips stalling through impact
                </h3>

                <div className="mt-5 grid gap-3">
                  {[
                    ["Evidence", "Your hips stop turning just before impact, so the arms flip the club through."],
                    ["Feel", "Feel your belt buckle keep rotating toward the target through the ball."],
                    ["Drill", "10 step-through swings, hips fully open at the finish."],
                  ].map(([label, body]) => (
                    <div key={label} className="rounded-xl border border-white/10 bg-white/5 p-3">
                      <p className="text-[11px] font-semibold uppercase tracking-wide text-[var(--color-amber)]">
                        {label}
                      </p>
                      <p className="mt-1 text-sm leading-snug text-white/80">{body}</p>
                    </div>
                  ))}
                </div>

                {/* rest of the ordered fix list */}
                <div className="mt-4 border-t border-white/10 pt-4">
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-white/40">
                    Next in your plan
                  </p>
                  <ul className="mt-2 space-y-1.5">
                    {[
                      ["2", "Trail arm lifting at the top"],
                      ["3", "Early release before impact"],
                    ].map(([n, label]) => (
                      <li key={n} className="flex items-center gap-2.5 text-sm text-white/70">
                        <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-white/10 text-[11px] font-semibold text-white/60">
                          {n}
                        </span>
                        {label}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* mini phase timeline */}
                <div className="mt-5 flex items-center gap-1.5">
                  {["Setup", "Takeaway", "Transition", "Impact", "Finish"].map((phase, i) => (
                    <div key={phase} className="flex-1">
                      <div
                        className={`h-1.5 rounded-full ${i === 3 ? "bg-[var(--color-amber)]" : "bg-white/15"}`}
                      />
                      <p className="mt-1.5 hidden text-center text-[9px] uppercase tracking-wide text-white/40 sm:block">
                        {phase}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </Reveal>
          </div>

          {/* marquee */}
          <div className="relative border-t border-white/10 py-4">
            <div className="flex w-max animate-marquee gap-3 whitespace-nowrap">
              {[...marqueeItems, ...marqueeItems].map((item, i) => (
                <span
                  key={`${item}-${i}`}
                  className="flex items-center gap-2 text-sm font-medium text-white/40"
                >
                  <Sparkles className="h-3.5 w-3.5 text-[var(--color-emerald)]" />
                  {item}
                </span>
              ))}
            </div>
          </div>
        </section>

        {/* ── Stats band ─────────────────────────────────────── */}
        <section className="border-b border-[var(--color-border)] bg-[var(--color-card)]">
          <div className="mx-auto grid max-w-6xl gap-y-8 px-4 py-12 text-center sm:grid-cols-2 lg:grid-cols-4">
            {[
              { stat: <AnimatedStat value={5} suffix=" phases" />, label: "read frame-by-frame, setup to finish" },
              { stat: <span className="tabular-nums">2–5 min</span>, label: "from upload to your full report" },
              { stat: <AnimatedStat value={100} suffix="%" />, label: "of findings tied to your own film" },
              { stat: <AnimatedStat value={30} suffix="-day" />, label: "private storage, then auto-deleted" },
            ].map((item, i) => (
              <Reveal key={i} delay={i * 80}>
                <p className="font-display text-4xl font-bold text-[var(--color-accent-deep)]">
                  {item.stat}
                </p>
                <p className="mx-auto mt-2 max-w-[16rem] text-sm text-[var(--color-muted)]">
                  {item.label}
                </p>
              </Reveal>
            ))}
          </div>
        </section>

        {/* ── What you receive (bento) ───────────────────────── */}
        <section className="mx-auto max-w-6xl px-4 py-20 sm:py-28">
          <Reveal className="max-w-2xl">
            <p className="flex items-center gap-2 text-sm font-semibold uppercase tracking-widest text-[var(--color-accent)]">
              <Gauge className="h-4 w-4" />
              What you receive
            </p>
            <h2 className="mt-3 font-display text-4xl font-bold leading-tight tracking-tight sm:text-5xl">
              A coach-style plan, not a pile of generic tips.
            </h2>
          </Reveal>

          <div className="mt-12 grid gap-5 sm:grid-cols-3">
            {deliverables.map((d, i) => {
              const Icon = d.icon;
              return (
                <Reveal
                  key={d.title}
                  delay={i * 90}
                  className={`group relative overflow-hidden rounded-3xl border border-[var(--color-border)] bg-[var(--color-card)] p-7 transition-all duration-300 hover:-translate-y-1.5 hover:border-[var(--color-emerald)]/40 hover:shadow-xl ${d.span}`}
                >
                  <div
                    className={`pointer-events-none absolute inset-0 bg-gradient-to-br ${d.glow} to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100`}
                  />
                  <div className="relative">
                    <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--color-accent-muted)] text-[var(--color-accent-deep)] transition-transform duration-300 group-hover:scale-110">
                      <Icon className="h-6 w-6" />
                    </span>
                    <h3 className="mt-5 font-display text-xl font-semibold">{d.title}</h3>
                    <p className="mt-2 leading-relaxed text-[var(--color-muted)]">{d.body}</p>
                  </div>
                </Reveal>
              );
            })}
          </div>
        </section>

        {/* ── How it works ───────────────────────────────────── */}
        <section className="relative overflow-hidden bg-[var(--color-sand)]">
          <div className="mx-auto max-w-6xl px-4 py-20 sm:py-28">
            <Reveal className="max-w-2xl">
              <p className="flex items-center gap-2 text-sm font-semibold uppercase tracking-widest text-[var(--color-accent)]">
                <Zap className="h-4 w-4" />
                How it works
              </p>
              <h2 className="mt-3 font-display text-4xl font-bold leading-tight tracking-tight sm:text-5xl">
                From a visible problem to a practice goal.
              </h2>
            </Reveal>

            <div className="relative mt-14 grid gap-8 md:grid-cols-3">
              {/* connecting line */}
              <div
                aria-hidden
                className="absolute left-0 right-0 top-7 hidden h-px bg-gradient-to-r from-[var(--color-emerald)]/50 via-[var(--color-lime)]/50 to-[var(--color-amber)]/50 md:block"
              />
              {steps.map((s, i) => {
                const Icon = s.icon;
                return (
                  <Reveal key={s.title} delay={i * 120} className="relative">
                    <div className="flex items-center gap-4">
                      <div className="relative flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-[var(--color-ink)] text-[var(--color-lime)] shadow-lg">
                        <Icon className="h-6 w-6" />
                      </div>
                      <span className="font-display text-5xl font-bold text-[var(--color-emerald)]/25">
                        {s.step}
                      </span>
                    </div>
                    <h3 className="mt-5 font-display text-xl font-semibold">{s.title}</h3>
                    <p className="mt-2 leading-relaxed text-[var(--color-muted)]">{s.body}</p>
                  </Reveal>
                );
              })}
            </div>
          </div>
        </section>

        {/* ── Live example report ────────────────────────────── */}
        <section className="mx-auto max-w-6xl px-4 py-20 sm:py-28">
          <div className="grid items-center gap-12 lg:grid-cols-[1fr_1.1fr]">
            <Reveal>
              <p className="flex items-center gap-2 text-sm font-semibold uppercase tracking-widest text-[var(--color-accent)]">
                <PlayCircle className="h-4 w-4" />
                See it before you buy
              </p>
              <h2 className="mt-3 font-display text-4xl font-bold leading-tight tracking-tight sm:text-5xl">
                A real, anonymized report.
              </h2>
              <p className="mt-4 leading-relaxed text-[var(--color-muted)]">
                This is exactly what lands in your account after an upload — your ordered fix list,
                the evidence from film, the feel and drill for each one, and your next-upload goal.
                No sign-up required to read it.
              </p>
              <Link href="/example" className="mt-7 inline-block">
                <Button className="group rounded-full">
                  View the full example report
                  <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                </Button>
              </Link>
            </Reveal>

            <Reveal delay={120} className="ring-gradient rounded-3xl bg-[var(--color-card)] p-7 shadow-xl">
              <p className="text-xs font-semibold uppercase tracking-widest text-[var(--color-accent)]">
                Anonymized real report example
              </p>
              <h3 className="mt-3 font-display text-2xl font-semibold">Fix 1 of 3: limited shoulder turn</h3>
              <div className="mt-6 grid gap-5 sm:grid-cols-2">
                {[
                  ["Evidence", "Your lead shoulder stops short of the ball at the top, cutting off width and power."],
                  ["Feel", "Feel your lead shoulder turn behind the ball until your back faces the target."],
                  ["Drill", "Ten slow cross-arm coil turns, then fifteen half-speed shots keeping that width."],
                  ["Next upload", "Confirm a fuller shoulder turn and matched hip depth from face-on."],
                ].map(([label, body]) => (
                  <div key={label}>
                    <p className="text-xs font-semibold uppercase tracking-wide text-[var(--color-muted)]">
                      {label}
                    </p>
                    <p className="mt-1 text-sm leading-relaxed text-[var(--color-muted)]">{body}</p>
                  </div>
                ))}
              </div>
            </Reveal>
          </div>
        </section>

        {/* ── Trust band ─────────────────────────────────────── */}
        <section className="bg-[var(--color-sand)]">
          <div className="mx-auto max-w-6xl px-4 py-20 sm:py-28">
            <div className="grid gap-5 sm:grid-cols-3">
              {trustPoints.map((t, i) => {
                const Icon = t.icon;
                return (
                  <Reveal
                    key={t.title}
                    delay={i * 90}
                    className="group rounded-3xl border border-[var(--color-border)] bg-[var(--color-card)] p-7 transition-all duration-300 hover:-translate-y-1 hover:shadow-lg"
                  >
                    <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-[var(--color-accent-muted)] text-[var(--color-accent-deep)]">
                      <Icon className="h-5 w-5" />
                    </span>
                    <h3 className="mt-4 font-display font-semibold">{t.title}</h3>
                    <p className="mt-2 text-sm leading-relaxed text-[var(--color-muted)]">{t.body}</p>
                  </Reveal>
                );
              })}
            </div>
          </div>
        </section>

        {/* ── Pricing ────────────────────────────────────────── */}
        <section className="mx-auto max-w-6xl px-4 py-20 sm:py-28">
          <Reveal className="mx-auto max-w-2xl text-center">
            <h2 className="font-display text-4xl font-bold leading-tight tracking-tight sm:text-5xl">
              Simple, honest pricing.
            </h2>
            <p className="mt-3 text-[var(--color-muted)]">Pay per swing, or go unlimited for the year.</p>
          </Reveal>

          <div className="mx-auto mt-12 grid max-w-3xl items-center gap-6 md:grid-cols-2">
            <Reveal className="flex flex-col rounded-3xl border border-[var(--color-border)] bg-[var(--color-card)] p-8 text-center">
              <h3 className="font-display text-lg font-semibold">Per swing</h3>
              <p className="mt-4 font-display text-5xl font-bold">{PRICE_PER_ANALYSIS_DISPLAY}</p>
              <p className="mt-1 text-sm text-[var(--color-muted)]">per video upload</p>
              <Link href="/signup?redirect=/upload" className="mt-6">
                <Button variant="secondary" className="w-full rounded-full">Analyze my swing</Button>
              </Link>
            </Reveal>

            <Reveal
              delay={120}
              className="ring-gradient relative flex flex-col rounded-3xl bg-[var(--color-ink)] p-8 text-center text-white shadow-2xl md:scale-[1.04]"
            >
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-r from-[var(--color-emerald)] to-[var(--color-lime)] px-4 py-1 text-xs font-bold uppercase tracking-wide text-[var(--color-ink)]">
                Best value
              </span>
              <h3 className="mt-2 font-display text-lg font-semibold">Unlimited annual</h3>
              <p className="mt-3 font-display text-5xl font-bold">
                {PRICE_ANNUAL_UNLIMITED_DISPLAY}
                <span className="text-lg font-medium text-white/60">/yr</span>
              </p>
              <p className="mt-1 text-sm text-white/60">unlimited uploads · cancel anytime</p>
              <Link href="/pricing" className="mt-6">
                <Button className="w-full animate-pulse-glow rounded-full bg-gradient-to-r from-[var(--color-emerald)] to-[var(--color-lime)] text-[var(--color-ink)]">
                  See plan details
                </Button>
              </Link>
            </Reveal>
          </div>
        </section>

        {/* ── FAQ ────────────────────────────────────────────── */}
        <section className="bg-[var(--color-sand)]">
          <div className="mx-auto max-w-3xl px-4 py-20 sm:py-28">
            <Reveal as="h2" className="text-center font-display text-4xl font-bold leading-tight tracking-tight sm:text-5xl">
              Questions golfers ask first
            </Reveal>
            <div className="mt-10 space-y-3">
              {faqs.map(([question, answer], i) => (
                <Reveal key={question} delay={i * 60}>
                  <details className="group rounded-2xl border border-[var(--color-border)] bg-[var(--color-card)] p-5 transition-colors open:border-[var(--color-emerald)]/40">
                    <summary className="flex cursor-pointer list-none items-center justify-between font-medium marker:content-['']">
                      {question}
                      <ChevronDown className="h-5 w-5 shrink-0 text-[var(--color-accent)] transition-transform duration-300 group-open:rotate-180" />
                    </summary>
                    <p className="mt-3 text-sm leading-relaxed text-[var(--color-muted)]">{answer}</p>
                  </details>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        {/* ── Final CTA ──────────────────────────────────────── */}
        <section className="relative overflow-hidden bg-[var(--color-ink)] px-4 py-24 text-center text-white sm:py-32">
          <div aria-hidden className="pointer-events-none absolute inset-0">
            <div
              className="blob absolute left-1/4 top-0 h-72 w-72 animate-float"
              style={{ background: "radial-gradient(circle, rgba(16,185,129,0.5), transparent 70%)" }}
            />
            <div
              className="blob absolute right-1/4 bottom-0 h-72 w-72 animate-float-slow"
              style={{ background: "radial-gradient(circle, rgba(245,158,11,0.35), transparent 70%)" }}
            />
          </div>
          <Reveal className="relative mx-auto max-w-2xl">
            <h2 className="font-display text-4xl font-bold leading-[1.05] tracking-tight sm:text-6xl">
              Give your next range session <span className="text-gradient">one clear purpose.</span>
            </h2>
            <Link href="/signup?redirect=/upload" className="mt-10 inline-block">
              <Button
                size="lg"
                className="group animate-pulse-glow rounded-full bg-gradient-to-r from-[var(--color-emerald)] to-[var(--color-lime)] text-[var(--color-ink)]"
              >
                Get my analysis — {PRICE_PER_ANALYSIS_DISPLAY}
                <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Button>
            </Link>
            <p className="mt-6 flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-sm text-white/60">
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="h-4 w-4 text-[var(--color-lime)]" />
                Private upload
              </span>
              <span className="flex items-center gap-1.5">
                <Clock className="h-4 w-4 text-[var(--color-lime)]" />
                Ready in 2–5 minutes
              </span>
              <span className="flex items-center gap-1.5">
                <RotateCcw className="h-4 w-4 text-[var(--color-lime)]" />
                Failed-analysis credit guarantee
              </span>
            </p>
          </Reveal>
        </section>
      </main>
    </div>
  );
}
