import { AppNav } from "@/components/AppNav";
import { ClearSwingHistoryButton, DeleteSwingButton } from "@/components/DeleteSwingButton";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/StatusBadge";
import { createClient } from "@/lib/supabase/server";
import type { SwingReport } from "@/lib/types";
import { getReportFocusLabel } from "@/lib/coaching";
import Link from "next/link";
import { redirect } from "next/navigation";

export default async function ProgressPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const { data: reports } = await supabase
    .from("swing_reports")
    .select("id, main_diagnosis, practice_plan, coaching_content, gemini_raw, created_at, status")
    .eq("user_id", user.id)
    .eq("status", "ready")
    .order("created_at", { ascending: false })
    .limit(20);

  return (
    <div className="min-h-screen">
      <AppNav />
      <main className="mx-auto max-w-6xl px-4 py-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold">Training history</h1>
            <p className="mt-1 text-[var(--color-muted)]">
              Your coaching blueprints and weekly focuses over time
            </p>
          </div>
          {reports && reports.length > 0 && <ClearSwingHistoryButton />}
        </div>

        <section className="mt-10">
          {!reports?.length ? (
            <Card className="text-center text-[var(--color-muted)]">No completed analyses yet.</Card>
          ) : (
            <>
              <div className="grid gap-3 md:hidden">
                {reports.map((r) => {
                  const report = r as SwingReport;
                  const focus = getReportFocusLabel(report);
                  return (
                    <Card key={r.id} className="p-4">
                      <p className="text-xs text-[var(--color-muted)]">
                        {new Date(r.created_at).toLocaleDateString()}
                      </p>
                      <p className="mt-2 font-medium">{focus || "Completed swing analysis"}</p>
                      <div className="mt-4 flex items-center justify-between gap-3">
                        <Link
                          href={`/swings/${r.id}`}
                          className="inline-flex min-h-11 items-center gap-2 text-sm text-[var(--color-accent)]"
                        >
                          <StatusBadge status="current_focus" />
                          Open report
                        </Link>
                        <DeleteSwingButton reportId={r.id} />
                      </div>
                    </Card>
                  );
                })}
              </div>
              <div className="hidden overflow-hidden rounded-lg border border-[var(--color-border)] md:block">
                <table className="w-full text-sm">
                <thead className="bg-[var(--color-card)]">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium">Date</th>
                    <th className="px-4 py-3 text-left font-medium">Weekly focus</th>
                    <th className="px-4 py-3 text-left font-medium">Blueprint</th>
                    <th className="px-4 py-3 text-right font-medium"> </th>
                  </tr>
                </thead>
                <tbody>
                  {reports.map((r) => {
                    const report = r as SwingReport;
                    const focus = getReportFocusLabel(report);
                    return (
                      <tr key={r.id} className="border-t border-[var(--color-border)]">
                        <td className="px-4 py-3">{new Date(r.created_at).toLocaleString()}</td>
                        <td className="px-4 py-3">
                          {focus ? (
                            <span className="font-medium text-[var(--color-accent)]">{focus}</span>
                          ) : (
                            "—"
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <Link href={`/swings/${r.id}`} className="inline-flex items-center gap-2 text-[var(--color-accent)] hover:underline">
                            <StatusBadge status="current_focus" />
                            Open
                          </Link>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <DeleteSwingButton reportId={r.id} />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
                </table>
              </div>
            </>
          )}
        </section>
      </main>
    </div>
  );
}
