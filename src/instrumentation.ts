import { captureServerError } from "@/lib/monitoring";

export async function register() {}

export const onRequestError = async (
  error: unknown,
  request: { path?: string; method?: string },
  context: { routerKind?: string; routeType?: string }
) => {
  await captureServerError(error, {
    path: request.path,
    method: request.method,
    routerKind: context.routerKind,
    routeType: context.routeType,
  });
};
