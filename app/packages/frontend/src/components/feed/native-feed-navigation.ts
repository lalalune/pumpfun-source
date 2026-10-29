import {
  NativeFeedDataError,
  validateNativeCursorInput,
  type NativeFeedKind,
} from "./native-feed-data";

/** Existing local URL-history bound; this is not a backend result limit. */
export const NATIVE_FEED_MAX_TRAIL = 20;

export type NativeFeedNavigation = {
  kind: NativeFeedKind;
  cursor?: string;
  trail: string[];
};

type NavigationParams = {
  nativeView?: string | string[];
  nativeCursor?: string | string[];
  nativeTrail?: string | string[];
};

function optionalSingle(
  value: string | string[] | undefined,
  label: string,
): string | undefined {
  if (Array.isArray(value)) {
    throw new NativeFeedDataError(`${label} must not be repeated`);
  }
  return value;
}

export function parseNativeFeedNavigation(
  params: NavigationParams,
): NativeFeedNavigation {
  const view = optionalSingle(params.nativeView, "nativeView") ?? "ranked";
  if (view !== "ranked" && view !== "newest") {
    throw new NativeFeedDataError("nativeView must be ranked or newest");
  }
  const cursor = validateNativeCursorInput(
    optionalSingle(params.nativeCursor, "nativeCursor"),
    "nativeCursor",
  );
  const rawTrail =
    params.nativeTrail === undefined
      ? []
      : Array.isArray(params.nativeTrail)
        ? params.nativeTrail
        : [params.nativeTrail];
  if (rawTrail.length > NATIVE_FEED_MAX_TRAIL) {
    throw new NativeFeedDataError("nativeTrail exceeds the local page bound");
  }
  const trail = Array.from(rawTrail, (value, index) => {
    const token = validateNativeCursorInput(value, `nativeTrail[${index}]`);
    if (token === undefined) throw new NativeFeedDataError("nativeTrail entries require a cursor");
    return token;
  });
  if (trail.length > 0 && !cursor) {
    throw new NativeFeedDataError("nativeTrail requires a current cursor");
  }
  if (
    new Set([...trail, ...(cursor ? [cursor] : [])]).size !==
    trail.length + (cursor ? 1 : 0)
  ) {
    throw new NativeFeedDataError("native pagination contains a cursor cycle");
  }
  return { kind: view, cursor, trail };
}

export function nativeFeedHref(
  kind: NativeFeedKind,
  cursor?: string,
  trail: readonly string[] = [],
): string {
  const query = new URLSearchParams({
    tab: "local-callouts",
    nativeView: kind,
  });
  if (cursor) query.set("nativeCursor", cursor);
  trail.forEach((token) => query.append("nativeTrail", token));
  return `/?${query}`;
}
