type AnalyticsProps = Record<string, string | number | boolean | undefined>;

declare global {
  interface Window {
    plausible?: (event: string, options?: { props?: AnalyticsProps }) => void;
  }
}

/** Fire a Plausible custom event when the script is loaded. No-ops without domain/script. */
export function trackEvent(name: string, props?: AnalyticsProps): void {
  if (typeof window === "undefined") return;
  if (!process.env.NEXT_PUBLIC_PLAUSIBLE_DOMAIN) return;
  try {
    window.plausible?.(name, props ? { props } : undefined);
  } catch {
    // Analytics must never break product flows.
  }
}
