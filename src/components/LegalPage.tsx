import { PublicHeader } from "@/components/PublicHeader";

export function LegalPage({
  title,
  updated = "June 19, 2026",
  children,
}: {
  title: string;
  updated?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen">
      <PublicHeader />
      <main className="mx-auto max-w-3xl px-4 py-12">
        <h1 className="text-3xl font-semibold">{title}</h1>
        <p className="mt-2 text-sm text-[var(--color-muted)]">Last updated: {updated}</p>
        <div className="mt-8 space-y-6 text-sm leading-7 text-[var(--color-muted)]">
          {children}
        </div>
      </main>
    </div>
  );
}
