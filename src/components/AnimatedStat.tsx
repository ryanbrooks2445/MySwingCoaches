"use client";

import { useEffect, useRef, useState } from "react";

interface AnimatedStatProps {
  /** Target numeric value to count up to. */
  value: number;
  prefix?: string;
  suffix?: string;
  /** Decimal places to render (e.g. 1 for "4.8"). */
  decimals?: number;
  durationMs?: number;
}

function prefersReducedMotion(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}

export function AnimatedStat({
  value,
  prefix = "",
  suffix = "",
  decimals = 0,
  durationMs = 1400,
}: AnimatedStatProps) {
  const ref = useRef<HTMLSpanElement | null>(null);
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    if (prefersReducedMotion() || typeof IntersectionObserver === "undefined") {
      setDisplay(value);
      return;
    }

    let frame = 0;
    let start = 0;

    const run = () => {
      const step = (now: number) => {
        if (!start) start = now;
        const progress = Math.min((now - start) / durationMs, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        setDisplay(value * eased);
        if (progress < 1) frame = requestAnimationFrame(step);
      };
      frame = requestAnimationFrame(step);
    };

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            run();
            observer.disconnect();
          }
        }
      },
      { threshold: 0.4 }
    );

    observer.observe(node);
    return () => {
      observer.disconnect();
      cancelAnimationFrame(frame);
    };
  }, [value, durationMs]);

  return (
    <span ref={ref} className="tabular-nums">
      {prefix}
      {display.toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      })}
      {suffix}
    </span>
  );
}
