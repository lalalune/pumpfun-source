// Maintained source reconstruction. Captured factories are never executed.
// Destination/fetch are explicit capabilities; import performs no request.
export class BalanceSummaryHttpError extends Error {
  status;
  retryAfterMs;
  constructor(message, status, options) {
    super(message);
    this.name = "BalanceSummaryHttpError";
    this.status = status;
    this.retryAfterMs = options?.retryAfterMs;
  }
}

function finiteProperty(value, key) {
  if (typeof value !== "object" || value === null) return;
  const field = value[key];
  return typeof field === "number" && Number.isFinite(field)
    ? field
    : undefined;
}
export const balanceSummaryStatus = (error) => finiteProperty(error, "status");
export const balanceSummaryRetryAfter = (error) =>
  finiteProperty(error, "retryAfterMs");

export function parseBalanceSummaryRetryAfter(header, nowMs = Date.now()) {
  if (!header) return;
  const text = header.trim();
  if (/^-?\d+$/.test(text)) {
    const seconds = Number(text);
    return seconds >= 0 ? 1000 * seconds : undefined;
  }
  const at = Date.parse(text);
  return Number.isNaN(at) ? undefined : Math.max(0, at - nowMs);
}

export function shouldRetryBalanceSummary(failureCount, error) {
  return balanceSummaryStatus(error) !== 401 && failureCount < 2;
}
export function balanceSummaryRetryDelay(failureCount, error) {
  if (balanceSummaryStatus(error) !== 429)
    return Math.min(1000 * 2 ** failureCount, 30000);
  const wait = balanceSummaryRetryAfter(error);
  return wait !== undefined ? Math.min(wait, 60000) : 5000 * (failureCount + 1);
}
export function balanceSummaryPollInterval(query) {
  const data = query.state.data;
  return query.state.status === "success" && data?.success === true
    ? 60000
    : 15000;
}
export const balanceSummaryQueryKey = (subject) => ["balanceSummary", subject];

export function createBalanceSummaryClient({
  fetchImplementation,
  baseUrl,
  nowMs = Date.now,
  memo,
  useQuery,
}) {
  if (typeof fetchImplementation !== "function" || typeof baseUrl !== "string")
    throw new TypeError(
      "An explicit fetch implementation and baseUrl are required",
    );

  async function read({ fetchOptions, userAddress, multiChain }) {
    // The original interpolates the subject before URL parsing; it does not
    // encode/validate it as a path segment. Do not silently repair that policy.
    const url = new URL(`${baseUrl}/${userAddress}`);
    if (multiChain) url.searchParams.set("multi_chain", "true");
    const response = await fetchImplementation(url.toString(), fetchOptions);
    if (response.status === 401)
      throw new BalanceSummaryHttpError("Unauthorized", 401);
    if (!response.ok)
      throw new BalanceSummaryHttpError(
        `Failed to fetch wallet summary (${response.status})`,
        response.status,
        {
          retryAfterMs:
            response.status === 429
              ? parseBalanceSummaryRetryAfter(
                  response.headers.get("retry-after"),
                  nowMs(),
                )
              : undefined,
        },
      );
    return response.json();
  }

  function queryOptions({ userAddress, fetchOptions }) {
    return {
      queryFn: () => read({ userAddress, multiChain: true, fetchOptions }),
      queryKey: balanceSummaryQueryKey(userAddress),
      retry: shouldRetryBalanceSummary,
      retryDelay: balanceSummaryRetryDelay,
    };
  }

  function useBalanceSummary({
    userAddress,
    fetchOptions,
    queryOptions: overrides,
  }) {
    if (typeof memo !== "function" || typeof useQuery !== "function")
      throw new TypeError(
        "Explicit compiler memo and query-hook ports are required",
      );
    const cache = memo(7);
    const enabled = !!userAddress;
    let base;
    if (cache[0] !== fetchOptions || cache[1] !== userAddress) {
      base = queryOptions({ userAddress, fetchOptions });
      cache[0] = fetchOptions;
      cache[1] = userAddress;
      cache[2] = base;
    } else base = cache[2];
    let options;
    if (cache[3] !== enabled || cache[4] !== overrides || cache[5] !== base) {
      options = {
        enabled,
        ...base,
        staleTime: Infinity,
        refetchOnMount: true,
        refetchOnWindowFocus: true,
        refetchOnReconnect: true,
        refetchInterval: balanceSummaryPollInterval,
        ...overrides,
      };
      cache[3] = enabled;
      cache[4] = overrides;
      cache[5] = base;
      cache[6] = options;
    } else options = cache[6];
    return useQuery(options);
  }
  return { read, queryOptions, useBalanceSummary };
}
