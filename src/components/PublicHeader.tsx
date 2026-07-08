import Link from "next/link";
import { APP_NAME } from "@/lib/brand";
import { Button } from "@/components/ui/Button";

export function PublicHeader() {
  return (
    <header className="border-b border-[var(--color-border)] bg-[var(--color-card)]">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-4">
        <Link href="/" className="shrink-0 text-base font-semibold tracking-tight sm:text-lg">
          {APP_NAME}
        </Link>
        <nav className="flex items-center gap-2 sm:gap-4" aria-label="Public navigation">
          <Link href="/pricing" className="hidden text-sm text-[var(--color-muted)] sm:block">
            Pricing
          </Link>
          <Link href="/login" className="whitespace-nowrap text-sm">
            Log in
          </Link>
          <Link href="/signup?redirect=/upload">
            <Button size="sm" className="whitespace-nowrap">Get started</Button>
          </Link>
        </nav>
      </div>
    </header>
  );
}
