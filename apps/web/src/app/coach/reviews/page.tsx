import Link from "next/link";
import { AppNav } from "@/components/AppNav";
import { Card } from "@/components/ui/Card";
import { SeverityBadge } from "@/components/ScoreRing";
import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";

export default async function CoachReviewsPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const { data: profile } = await supabase
    .from("profiles")
    .select("role")
    .eq("id", user.id)
    .single();

  if (!profile || !["coach", "admin"].includes(profile.role)) {
    redirect("/dashboard");
  }

  const { data: reviews } = await supabase
    .from("coach_reviews")
    .select(`
      *,
      swing_reports(id, overall_score, main_diagnosis, status),
      profiles!coach_reviews_user_id_fkey(display_name)
    `)
    .order("created_at", { ascending: false })
    .limit(50);

  const { data: pendingReports } = await supabase
    .from("swing_reports")
    .select("id, user_id, overall_score, created_at, status, profiles(display_name)")
    .eq("status", "ready")
    .order("created_at", { ascending: false })
    .limit(20);

  return (
    <div className="min-h-screen">
      <AppNav />
      <main className="mx-auto max-w-6xl px-4 py-8">
        <h1 className="text-3xl font-semibold">Coach review queue</h1>
        <p className="mt-1 text-[var(--color-muted)]">Review AI reports and add human notes</p>

        <section className="mt-8">
          <h2 className="mb-4 text-xl font-semibold">Pending reviews</h2>
          {!reviews?.filter((r) => r.status !== "completed").length ? (
            <Card className="text-[var(--color-muted)]">No pending coach reviews.</Card>
          ) : (
            <div className="grid gap-4">
              {reviews
                ?.filter((r) => r.status !== "completed")
                .map((review) => (
                  <Link key={review.id} href={`/coach/reviews/${review.report_id}`}>
                    <Card className="transition-shadow hover:shadow-md">
                      <div className="flex justify-between">
                        <div>
                          <p className="font-medium">Review #{review.id.slice(0, 8)}</p>
                          <p className="text-sm capitalize text-[var(--color-muted)]">{review.status}</p>
                        </div>
                        <span className="text-sm text-[var(--color-accent)]">Open →</span>
                      </div>
                    </Card>
                  </Link>
                ))}
            </div>
          )}
        </section>

        <section className="mt-10">
          <h2 className="mb-4 text-xl font-semibold">Recent AI reports</h2>
          <div className="grid gap-4">
            {pendingReports?.map((report) => (
              <Link key={report.id} href={`/coach/reviews/${report.id}`}>
                <Card className="transition-shadow hover:shadow-md">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">
                        {(report.profiles as { display_name?: string } | null)?.display_name ?? "Golfer"}
                      </p>
                      <p className="text-sm text-[var(--color-muted)]">
                        {new Date(report.created_at).toLocaleString()}
                      </p>
                    </div>
                    <p className="text-2xl font-semibold text-[var(--color-accent)]">
                      {report.overall_score ?? "—"}
                    </p>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
