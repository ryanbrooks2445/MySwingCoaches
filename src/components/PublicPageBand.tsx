import { cn } from "@/lib/utils";

interface PublicPageBandProps {
  children: React.ReactNode;
  className?: string;
  variant?: "default" | "sand" | "ink";
}

export function PublicPageBand({
  children,
  className,
  variant = "default",
}: PublicPageBandProps) {
  return (
    <div
      className={cn(
        variant === "sand" && "bg-[var(--color-sand)]",
        variant === "ink" && "relative overflow-hidden bg-[var(--color-ink)] text-white"
      )}
    >
      {variant === "ink" && (
        <div aria-hidden className="pointer-events-none absolute inset-0">
          <div
            className="blob absolute left-1/4 top-0 h-64 w-64 animate-float"
            style={{ background: "radial-gradient(circle, rgba(16,185,129,0.4), transparent 70%)" }}
          />
          <div
            className="blob absolute right-1/4 bottom-0 h-64 w-64 animate-float-slow"
            style={{ background: "radial-gradient(circle, rgba(245,158,11,0.25), transparent 70%)" }}
          />
        </div>
      )}
      <div className={cn("relative", className)}>{children}</div>
    </div>
  );
}
