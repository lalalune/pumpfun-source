// Independent303599 read/query/membership boundaries. A viewer key is a request
// value supplied by the host, not a session or ownership assertion.
import { UserFetchError } from "../profile-lookup/client.mjs";
export const viewerFollowingKey = (viewerKey) => [
  "viewer-following",
  viewerKey,
];

export function parseViewerFollowingText(text) {
  let value;
  try {
    value = JSON.parse(text);
  } catch {
    throw new UserFetchError({ reason: "invalid_json" });
  }
  if (!Array.isArray(value))
    throw new UserFetchError({ reason: "invalid_shape" });
  return value;
}
export async function requireViewerFollowingResponse(
  _request,
  _options,
  response,
) {
  if (!response.ok)
    throw Error(`Failed to fetch viewer following list: ${response.status}`);
  if (!(await response.clone().text()).trim())
    throw new UserFetchError({ reason: "empty_body" });
}
export function viewerFollowingQueryOptions(transport, viewerKey) {
  return {
    queryKey: viewerFollowingKey(viewerKey),
    queryFn: async ({ signal }) => {
      if (!viewerKey) return [];
      const value = await transport("GET /following/v3/following/{userId}", {
        params: { userId: viewerKey },
        query: { limit: 1000 },
        signal,
        throwHttpErrors: false,
        hooks: { afterResponse: [requireViewerFollowingResponse] },
        parseJson: parseViewerFollowingText,
      });
      if (value === null) throw new UserFetchError({ reason: "invalid_shape" });
      return value;
    },
    staleTime: 60000,
    gcTime: 300000,
    refetchOnWindowFocus: (query) => query.state.status === "error",
  };
}
export function viewerFollowingSet(rows) {
  const values = new Set();
  for (const row of rows ?? []) {
    if (typeof row?.address === "string" && row.address)
      values.add(row.address.toLowerCase());
    const id = row?.user_id ?? row?.userId;
    if (typeof id === "string" && id) values.add(id.toLowerCase());
  }
  return values;
}
export function activeViewerFollowingOptions(transport, viewerKey, options) {
  return {
    ...viewerFollowingQueryOptions(transport, viewerKey),
    enabled: (options?.enabled ?? true) && !!viewerKey,
  };
}
export function passiveViewerFollowingOptions(transport, viewerKey) {
  return {
    ...viewerFollowingQueryOptions(transport, viewerKey),
    enabled: false,
  };
}
export function viewerFollowingState(viewerKey, options, query) {
  const enabled = (options?.enabled ?? true) && !!viewerKey;
  const followingSet = viewerFollowingSet(query.data);
  const ready = enabled && query.isSuccess;
  return {
    ready,
    isError: query.isError,
    followingSet,
    isFollowing: (identifier) => {
      if (ready && identifier)
        return followingSet.has(identifier.toLowerCase());
    },
  };
}
export function passiveFollowingMembership(viewerKey, identifier, query) {
  const values = viewerFollowingSet(query.data);
  if (viewerKey && identifier && query.isSuccess)
    return values.has(identifier.toLowerCase());
}
