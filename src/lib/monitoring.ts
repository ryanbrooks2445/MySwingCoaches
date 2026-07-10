import * as Sentry from "@sentry/nextjs";

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
  const dsn = process.env.SENTRY_DSN?.trim() || process.env.NEXT_PUBLIC_SENTRY_DSN?.trim();
  if (!dsn) return;

  try {
    Sentry.captureException(error, {
      tags: {
        method: context.method,
        router_kind: context.routerKind,
        route_type: context.routeType,
      },
      extra: {
        path: context.path,
      },
    });
    await Sentry.flush(2000);
  } catch {
    // Monitoring must never turn an application error into a second failure.
  }
}
