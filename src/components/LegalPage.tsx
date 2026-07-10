import { PublicHeader } from "@/components/PublicHeader";
import { PageHero } from "@/components/PageHero";
import { Card } from "@/components/ui/Card";
import { Reveal } from "@/components/Reveal";

export function LegalPage({
  title,
  updated = "June 19, 2026",
  description,
  children,
}: {
  title: string;
  updated?: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[var(--color-background)]">
      <PublicHeader />
      <main id="main-content" className="mx-auto max-w-3xl px-4 py-12 sm:py-16">
        <Reveal immediate>
          <PageHero title={title} description={description} />
          <p className="mt-4 text-sm text-[var(--color-muted)]">Last updated: {updated}</p>
        </Reveal>
        <Reveal immediate>
          <Card className="mt-10 rounded-3xl">
            <div className="space-y-6 text-sm leading-7 text-[var(--color-muted)] [&_a]:font-medium [&_a]:text-[var(--color-accent)] [&_a]:hover:underline [&_h2]:font-display [&_h2]:text-lg [&_h2]:font-semibold [&_h2]:text-[var(--color-foreground)] [&_h3]:font-medium [&_h3]:text-[var(--color-foreground)] [&_li]:ml-4 [&_ol]:list-decimal [&_ul]:list-disc">
              {children}
            </div>
          </Card>
        </Reveal>
      </main>
    </div>
  );
}
