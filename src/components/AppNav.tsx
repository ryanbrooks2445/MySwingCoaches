"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { Menu } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { createClient } from "@/lib/supabase/client";
import { cn } from "@/lib/utils";

const links = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/upload", label: "Upload" },
  { href: "/progress", label: "Progress" },
  { href: "/pricing", label: "Pricing" },
  { href: "/account", label: "Account" },
];

export function AppNav() {
  const pathname = usePathname();
  const router = useRouter();
  const [signingOut, setSigningOut] = useState(false);

  async function handleSignOut() {
    setSigningOut(true);
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
    router.refresh();
  }

  return (
    <header className="border-b border-[var(--color-border)] bg-[var(--color-card)]/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
        <Link href="/dashboard" className="text-lg font-semibold tracking-tight">
          ForeFixed
        </Link>
        <nav className="hidden items-center gap-5 md:flex">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "text-sm transition-colors",
                pathname === link.href
                  ? "font-medium text-[var(--color-foreground)]"
                  : "text-[var(--color-muted)] hover:text-[var(--color-foreground)]"
              )}
            >
              {link.label}
            </Link>
          ))}
          <Button
            type="button"
            variant="ghost"
            size="sm"
            disabled={signingOut}
            onClick={handleSignOut}
            className="text-[var(--color-muted)]"
          >
            {signingOut ? "Signing out…" : "Sign out"}
          </Button>
        </nav>
        <details className="relative md:hidden">
          <summary
            className="flex h-11 w-11 cursor-pointer list-none items-center justify-center rounded-lg border border-[var(--color-border)]"
            aria-label="Open navigation"
          >
            <Menu className="h-5 w-5" />
          </summary>
          <nav className="absolute right-0 z-20 mt-2 w-52 rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] p-2 shadow-lg">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "block rounded-md px-3 py-3 text-sm",
                  pathname === link.href
                    ? "bg-[var(--color-accent-muted)] font-medium"
                    : "text-[var(--color-muted)]"
                )}
              >
                {link.label}
              </Link>
            ))}
            <button
              type="button"
              disabled={signingOut}
              onClick={handleSignOut}
              className="block w-full rounded-md px-3 py-3 text-left text-sm text-[var(--color-muted)]"
            >
              {signingOut ? "Signing out…" : "Sign out"}
            </button>
          </nav>
        </details>
      </div>
    </header>
  );
}
