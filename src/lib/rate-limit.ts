import { NextRequest, NextResponse } from "next/server";

type WindowEntry = { count: number; resetAt: number };
const memoryWindows = new Map<string, WindowEntry>();

function clientIp(request: NextRequest): string {
  return (
    request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ||
    request.headers.get("x-real-ip") ||
    "unknown"
  );
}

function enforceMemoryRateLimit(
  key: string,
  limit: number,
  windowSeconds: number
): NextResponse | null {
  const now = Date.now();
  const current = memoryWindows.get(key);
  if (!current || current.resetAt <= now) {
    memoryWindows.set(key, {
      count: 1,
      resetAt: now + windowSeconds * 1000,
    });
    return null;
  }

  current.count += 1;
  if (current.count <= limit) return null;

  return NextResponse.json(
    { error: "Too many requests. Please wait and try again." },
    {
      status: 429,
      headers: { "Retry-After": String(Math.ceil((current.resetAt - now) / 1000)) },
    }
  );
}

export async function enforceRateLimit(
  request: NextRequest,
  options: {
    scope: string;
    identifier?: string;
    limit: number;
    windowSeconds: number;
  }
): Promise<NextResponse | null> {
  const key = `${options.scope}:${options.identifier || clientIp(request)}`;
  const upstashUrl = process.env.UPSTASH_REDIS_REST_URL?.replace(/\/$/, "");
  const upstashToken = process.env.UPSTASH_REDIS_REST_TOKEN;
  const isProduction = process.env.NODE_ENV === "production";

  if (upstashUrl && upstashToken) {
    try {
      const response = await fetch(`${upstashUrl}/pipeline`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${upstashToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify([
          ["INCR", key],
          ["EXPIRE", key, String(options.windowSeconds), "NX"],
        ]),
        cache: "no-store",
      });
      if (response.ok) {
        const result = (await response.json()) as Array<{ result?: number }>;
        if ((result[0]?.result ?? 0) > options.limit) {
          return NextResponse.json(
            { error: "Too many requests. Please wait and try again." },
            { status: 429, headers: { "Retry-After": String(options.windowSeconds) } }
          );
        }
        return null;
      }
      console.warn("rate_limit_provider_unavailable", {
        scope: options.scope,
        status: response.status,
      });
      if (isProduction) {
        return NextResponse.json(
          { error: "Service temporarily unavailable. Please try again shortly." },
          { status: 503 }
        );
      }
    } catch {
      console.warn("rate_limit_provider_unreachable", { scope: options.scope });
      if (isProduction) {
        return NextResponse.json(
          { error: "Service temporarily unavailable. Please try again shortly." },
          { status: 503 }
        );
      }
    }
  } else if (isProduction) {
    console.error("rate_limit_upstash_not_configured", { scope: options.scope });
    return NextResponse.json(
      { error: "Service temporarily unavailable. Please try again shortly." },
      { status: 503 }
    );
  } else {
    console.warn("rate_limit_upstash_not_configured", { scope: options.scope });
  }

  return enforceMemoryRateLimit(key, options.limit, options.windowSeconds);
}
