import { cn } from "@/lib/utils";

interface PageHeroProps {
  eyebrow?: string;
  title: string;
  description?: string;
  className?: string;
  centered?: boolean;
  dark?: boolean;
}

export function PageHero({
  eyebrow,
  title,
  description,
  className,
  centered = false,
  dark = false,
}: PageHeroProps) {
  return (
    <header
      className={cn(
        centered && "text-center",
        className
      )}
    >
      {eyebrow && (
        <p
          className={cn(
            "text-sm font-semibold uppercase tracking-widest",
            dark ? "text-[var(--color-lime)]" : "text-[var(--color-accent)]"
          )}
        >
          {eyebrow}
        </p>
      )}
      <h1
        className={cn(
          "font-display font-bold leading-tight tracking-tight",
          eyebrow ? "mt-3" : "",
          dark ? "text-white" : "text-[var(--color-foreground)]",
          centered ? "text-4xl sm:text-5xl" : "text-3xl sm:text-4xl"
        )}
      >
        {title}
      </h1>
      {description && (
        <p
          className={cn(
            "mt-3 max-w-2xl text-base leading-relaxed",
            dark ? "text-white/70" : "text-[var(--color-muted)]",
            centered && "mx-auto"
          )}
        >
          {description}
        </p>
      )}
    </header>
  );
}
