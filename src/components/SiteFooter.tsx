import Link from "next/link";
import { APP_NAME } from "@/lib/brand";

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
    <footer className="mt-auto border-t border-[var(--color-border)] bg-[var(--color-sand)]">
      <div className="mx-auto max-w-6xl px-4 py-10">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="font-display text-base font-bold tracking-tight">{APP_NAME}</p>
            <p className="mt-2 max-w-sm text-sm leading-relaxed text-[var(--color-muted)]">
              AI-assisted golf coaching guidance — prioritized fixes, evidence from your film, and
              drills you can use at the range.
            </p>
          </div>
          <nav className="flex flex-wrap gap-x-5 gap-y-2 text-sm" aria-label="Legal and support">
            {links.map(([label, href]) => (
              <Link
                key={href}
                href={href}
                className="text-[var(--color-muted)] transition-colors hover:text-[var(--color-foreground)]"
              >
                {label}
              </Link>
            ))}
          </nav>
        </div>
        <p className="mt-8 border-t border-[var(--color-border)] pt-6 text-xs text-[var(--color-muted)]">
          © {new Date().getFullYear()} {APP_NAME}. Not a replacement for in-person PGA instruction.
        </p>
      </div>
    </footer>
  );
}
