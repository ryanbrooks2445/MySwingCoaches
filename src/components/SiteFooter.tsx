import Link from "next/link";

const links = [
  ["Terms", "/terms"],
  ["Privacy", "/privacy"],
  ["Refunds", "/refund-policy"],
  ["Video retention", "/video-retention"],
  ["Support", "/support"],
  ["Contact", "/contact"],
];

export function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-[var(--color-border)] bg-[var(--color-card)]">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-8 text-sm text-[var(--color-muted)] sm:flex-row sm:items-center sm:justify-between">
        <p>© {new Date().getFullYear()} ForeFixed. MySwingCoaches is AI-assisted guidance.</p>
        <nav className="flex flex-wrap gap-x-4 gap-y-2" aria-label="Legal and support">
          {links.map(([label, href]) => (
            <Link key={href} href={href} className="hover:text-[var(--color-foreground)]">
              {label}
            </Link>
          ))}
        </nav>
      </div>
    </footer>
  );
}
