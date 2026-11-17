export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`/api/backend/${path}`, {
    ...options,
    cache: "no-store",
    signal: AbortSignal.timeout(240_000),
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    if (body?.detail?.code === "credit_balance_exhausted")
      throw new Error(
        "The answer service has no remaining API credit. Try again after credit is restored.",
      );
    if (response.status === 404)
      throw new Error("This report was not found in the indexed corpus.");
    if (response.status === 422)
      throw new Error(
        "Please enter a question between 1 and 2,000 characters.",
      );
    throw new Error(
      "The report service could not complete this request. Please try again when the service is available.",
    );
  }
  return body as T;
}
