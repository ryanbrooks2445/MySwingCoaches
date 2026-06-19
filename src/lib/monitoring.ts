interface ServerErrorContext {
  path?: string;
  method?: string;
  routerKind?: string;
  routeType?: string;
}

export async function captureServerError(
  error: unknown,
  context: ServerErrorContext = {}
): Promise<void> {
  const dsn = process.env.SENTRY_DSN?.trim();
  if (!dsn) return;

  try {
    const parsed = new URL(dsn);
    const projectId = parsed.pathname.replace("/", "");
    const endpoint = `${parsed.protocol}//${parsed.host}/api/${projectId}/store/`;
    const message = error instanceof Error ? error.message : String(error);

    await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Sentry-Auth": [
          "Sentry sentry_version=7",
          `sentry_key=${parsed.username}`,
          "sentry_client=myswingcoaches-next/1.0",
        ].join(", "),
      },
      body: JSON.stringify({
        event_id: crypto.randomUUID().replaceAll("-", ""),
        timestamp: new Date().toISOString(),
        platform: "javascript",
        level: "error",
        message,
        tags: {
          method: context.method,
          router_kind: context.routerKind,
          route_type: context.routeType,
        },
        request: { url: context.path },
      }),
    });
  } catch {
    // Monitoring must never turn an application error into a second failure.
  }
}
