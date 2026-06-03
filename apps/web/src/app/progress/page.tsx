import { AppNav } from "@/components/AppNav";
import { ProgressChart } from "@/components/ProgressChart";
import { Card } from "@/components/ui/Card";
import { createClient } from "@/lib/supabase/server";
import Link from "next/link";
import { redirect } from "next/navigation";

export default async function ProgressPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const { data: reports } = await supabase
    .from("swing_reports")
    .select("id, overall_score, created_at, status")
    .eq("user_id", user.id)
    .eq("status", "ready")
    .order("created_at", { ascending: true })
    .limit(20);

  const chartData = (reports ?? [])
    .filter((r) => r.overall_score != null)
    .map((r) => ({
      date: new Date(r.created_at).toLocaleDateString(),
      score: r.overall_score as number,
    }));

  return (
    <div className="min-h-screen">
      <AppNav />
      <main className="mx-auto max-w-6xl px-4 py-8">
        <h1 className="text-3xl font-semibold">Progress</h1>
        <p className="mt-1 text-[var(--color-muted)]">Track your swing scores over time</p>

        <Card className="mt-8">
          <ProgressChart data={chartData} />
        </Card>

        <section className="mt-10">
          <h2 className="mb-4 text-xl font-semibold">History</h2>
          {!reports?.length ? (
            <Card className="text-center text-[var(--color-muted)]">No completed analyses yet.</Card>
          ) : (
            <div className="overflow-hidden rounded-xl border border-[var(--color-border)]">
              <table className="w-full text-sm">
                <thead className="bg-[var(--color-card)]">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium">Date</th>
                    <th className="px-4 py-3 text-left font-medium">Score</th>
                    <th className="px-4 py-3 text-left font-medium">Report</th>
                  </tr>
                </thead>
                <tbody>
                  {[...(reports ?? [])].reverse().map((r) => (
                    <tr key={r.id} className="border-t border-[var(--color-border)]">
                      <td className="px-4 py-3">{new Date(r.created_at).toLocaleString()}</td>
                      <td className="px-4 py-3 font-medium text-[var(--color-accent)]">
                        {r.overall_score ?? "—"}
                      </td>
                      <td className="px-4 py-3">
                        <Link href={`/swings/${r.id}`} className="text-[var(--color-accent)] hover:underline">
                          View report
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
