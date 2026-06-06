type TraceFields = {
  trace_id?: string | null;
  user_id?: string | null;
  report_id?: string | null;
  status?: string | null;
  error?: string | null;
  [key: string]: unknown;
};

export function logTrace(event: string, fields: TraceFields = {}): void {
  const payload = {
    event,
    trace_id: fields.trace_id ?? null,
    user_id: fields.user_id ?? null,
    report_id: fields.report_id ?? null,
    status: fields.status ?? null,
    error: fields.error ?? null,
    timestamp: new Date().toISOString(),
    ...Object.fromEntries(
      Object.entries(fields).filter(
        ([key]) => !["trace_id", "user_id", "report_id", "status", "error"].includes(key)
      )
    ),
  };
  console.info(JSON.stringify(payload));
}
