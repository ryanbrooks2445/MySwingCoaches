import Link from "next/link";
import { AppNav } from "@/components/AppNav";
import { SwingCard } from "@/components/SwingCard";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ScoreRing } from "@/components/ScoreRing";
import { createClient } from "@/lib/supabase/server";
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

  const latestScore = reports?.[0]?.overall_score ?? null;
  const avgScore =
    reports?.filter((r) => r.overall_score != null).length
      ? Math.round(
          reports!.reduce((s, r) => s + (r.overall_score ?? 0), 0) /
            reports!.filter((r) => r.overall_score != null).length
        )
      : null;

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
                ? `${subscription.analyses_used} / ${subscription.analyses_limit === -1 ? "∞" : subscription.analyses_limit} analyses used (${subscription.plan} plan)`
                : "Free plan"}
            </p>
          </div>
          <Link href="/upload">
            <Button>Upload swing</Button>
          </Link>
        </div>

        <div className="mt-8 grid gap-6 md:grid-cols-3">
          <Card className="relative flex flex-col items-center">
            <ScoreRing score={latestScore} label="Latest score" />
          </Card>
          <Card className="relative flex flex-col items-center">
            <ScoreRing score={avgScore} label="Average score" />
          </Card>
          <Card>
            <p className="text-sm text-[var(--color-muted)]">Total swings</p>
            <p className="mt-2 text-4xl font-semibold">{reports?.length ?? 0}</p>
            <Link href="/progress" className="mt-4 inline-block text-sm text-[var(--color-accent)] hover:underline">
              View progress →
            </Link>
          </Card>
        </div>

        <section className="mt-10">
          <h2 className="mb-4 text-xl font-semibold">Recent swings</h2>
          {!reports?.length ? (
            <Card className="text-center">
              <p className="text-[var(--color-muted)]">No swings yet. Upload your first video to get started.</p>
              <Link href="/upload" className="mt-4 inline-block">
                <Button>Upload swing</Button>
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
