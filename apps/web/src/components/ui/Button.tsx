import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
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
        "inline-flex items-center justify-center rounded-full font-medium transition-colors disabled:opacity-50",
        variant === "primary" && "bg-[var(--color-accent)] text-white hover:opacity-90",
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
