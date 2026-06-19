export async function readApiResponse<T extends Record<string, unknown>>(
  response: Response
): Promise<T & { error?: string }> {
  const contentType = response.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    const text = (await response.text()).trim();
    if (!text) {
      return {} as T & { error?: string };
    }
    return JSON.parse(text) as T & { error?: string };
  }

  const text = (await response.text()).trim();
  return {
    error:
      text ||
      `Request failed with status ${response.status}. Please refresh and try again.`,
  } as T & { error?: string };
}
