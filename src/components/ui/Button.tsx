import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "cta";
  size?: "sm" | "md" | "lg";
}

export function Button({
  className,
  variant = "primary",
  size = "md",
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-xl font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
        variant === "primary" && "bg-[var(--color-accent)] text-white hover:opacity-90",
        variant === "cta" &&
          "rounded-full bg-gradient-to-r from-[var(--color-emerald)] to-[var(--color-lime)] text-[var(--color-ink)] hover:opacity-90",
        variant === "secondary" && "border border-[var(--color-border)] bg-[var(--color-card)] hover:bg-[var(--color-border)]/30",
        variant === "ghost" && "hover:bg-[var(--color-border)]/30",
        size === "sm" && "px-4 py-2 text-sm",
        size === "md" && "px-6 py-2.5 text-sm",
        size === "lg" && "px-8 py-3 text-base",
        className
      )}
      {...props}
    />
  );
}
