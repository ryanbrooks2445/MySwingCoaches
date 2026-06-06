import Link from "next/link";
import { AppNav } from "@/components/AppNav";
import { SwingCard } from "@/components/SwingCard";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/StatusBadge";
import { createClient } from "@/lib/supabase/server";
import { analysisCreditsRemaining } from "@/lib/subscription";
import { PRICE_PER_ANALYSIS_DISPLAY } from "@/lib/pricing";
import { getReportFocusLabel } from "@/lib/coaching";
import type { SwingReport } from "@/lib/types";
import { redirect } from "next/navigation";

export default async function DashboardPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const { data: profile } = await supabase
    .from("profiles")
    .select("*")
    .eq("id", user.id)
    .single();

  const { data: subscription } = await supabase
    .from("subscriptions")
    .select("*")
    .eq("user_id", user.id)
    .single();

  const { data: reports } = await supabase
    .from("swing_reports")
    .select("*, swing_videos(*)")
    .eq("user_id", user.id)
    .order("created_at", { ascending: false })
    .limit(10);

  const latest = reports?.[0] as SwingReport | undefined;
  const currentFocus = latest ? getReportFocusLabel(latest) : null;

  return (
    <div className="min-h-screen">
      <AppNav />
      <main className="mx-auto max-w-6xl px-4 py-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold">
              Welcome{profile?.display_name ? `, ${profile.display_name}` : ""}
            </h1>
            <p className="mt-1 text-[var(--color-muted)]">
              {subscription
                ? (() => {
                    const remaining = analysisCreditsRemaining(subscription);
                    if (remaining === "unlimited") return "Unlimited analyses";
                    return `${remaining} upload${remaining === 1 ? "" : "s"} ready · ${PRICE_PER_ANALYSIS_DISPLAY} each`;
                  })()
                : `Buy an analysis — ${PRICE_PER_ANALYSIS_DISPLAY}`}
            </p>
          </div>
          <Link href="/upload">
            <Button>Upload Swing</Button>
          </Link>
        </div>

        <div className="mt-8 grid gap-6 md:grid-cols-3">
          <Card className="md:col-span-2">
            <p className="text-sm text-[var(--color-muted)]">
              {currentFocus ? "Your Focus" : "Get Started"}
            </p>
            {currentFocus ? (
              <>
                <p className="mt-2 text-2xl font-semibold">{currentFocus}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  <StatusBadge status="current_focus" />
                  {latest?.id && (
                    <Link
                      href={`/swings/${latest.id}`}
                      className="text-sm text-[var(--color-accent)] hover:underline"
                    >
                      Open analysis →
                    </Link>
                  )}
                </div>
              </>
            ) : (
              <p className="mt-2 text-[var(--color-muted)]">
                Upload a swing to get your coaching analysis and 7-day plan.
              </p>
            )}
          </Card>
          <Card>
            <p className="text-sm text-[var(--color-muted)]">Swings Analyzed</p>
            <p className="mt-2 text-4xl font-semibold">{reports?.length ?? 0}</p>
            <Link href="/progress" className="mt-4 inline-block text-sm text-[var(--color-accent)] hover:underline">
              View history →
            </Link>
          </Card>
        </div>

        <section className="mt-10">
          <h2 className="mb-4 text-xl font-semibold">Recent Swings</h2>
          {!reports?.length ? (
            <Card className="text-center">
              <p className="text-[var(--color-muted)]">No swings yet. Upload your first video to get started.</p>
              <Link href="/upload" className="mt-4 inline-block">
                <Button>Upload Swing</Button>
              </Link>
            </Card>
          ) : (
            <div className="grid gap-4">
              {reports.map((report) => (
                <SwingCard
                  key={report.id}
                  video={report.swing_videos as never}
                  report={report}
                />
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
