import Link from "next/link";
import { APP_NAME } from "@/lib/brand";
import { Button } from "@/components/ui/Button";

export function PublicHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-card)]/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-4">
        <Link
          href="/"
          className="shrink-0 font-display text-base font-bold tracking-tight sm:text-lg"
        >
          {APP_NAME}
        </Link>
        <nav className="flex items-center gap-2 sm:gap-4" aria-label="Public navigation">
          <Link
            href="/example"
            className="hidden text-sm text-[var(--color-foreground)]/70 transition-colors hover:text-[var(--color-foreground)] sm:block"
          >
            Example
          </Link>
          <Link
            href="/pricing"
            className="hidden text-sm text-[var(--color-foreground)]/70 transition-colors hover:text-[var(--color-foreground)] sm:block"
          >
            Pricing
          </Link>
          <Link
            href="/login"
            className="whitespace-nowrap text-sm font-medium transition-colors hover:text-[var(--color-accent-deep)]"
          >
            Log in
          </Link>
          <Link href="/signup?redirect=/upload">
            <Button
              size="sm"
              className="whitespace-nowrap rounded-full bg-gradient-to-r from-[var(--color-emerald)] to-[var(--color-lime)] text-[var(--color-ink)] hover:opacity-90"
            >
              Get started
            </Button>
          </Link>
        </nav>
      </div>
    </header>
  );
}
