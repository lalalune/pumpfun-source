import "server-only";

import {
  NATIVE_FEED_COMPATIBILITY,
  NATIVE_FEED_DATA_SOURCE,
  NativeFeedDataError,
  validateNativeFeedPage,
  validateNativeNewCount,
  validateNativeCursorInput,
  type NativeFeedKind,
  type NativeFeedPage,
  type NativeNewCount,
} from "./native-feed-data";

const LOCAL_BACKEND_ORIGIN = "http://127.0.0.1:3001";
const LOCAL_BACKEND_TIMEOUT_MS = 2_000;

export type NativeFeedLoadResult =
  | {
      ok: true;
      page: NativeFeedPage;
      count?: NativeNewCount;
    }
  | {
      ok: false;
      reason:
        | "disabled"
        | "invalid-cursor"
        | "unavailable"
        | "invalid-response";
      message: string;
    };

export function isNativeFeedEnabled(): boolean {
  return process.env.PUMP_LOCAL_HOME_FEED === "enabled";
}

async function readLocalJson(path: string): Promise<unknown> {
  const url = new URL(path, LOCAL_BACKEND_ORIGIN);
  let response: Response;
  try {
    response = await fetch(url, {
      method: "GET",
      cache: "no-store",
      credentials: "omit",
      headers: { accept: "application/json" },
      signal: AbortSignal.timeout(LOCAL_BACKEND_TIMEOUT_MS),
    });
  } catch {
    throw new NativeFeedDataError("The local Home Feed backend is unavailable");
  }
  if (response.status !== 200) {
    if (response.status === 400) {
      throw new NativeFeedDataError(
        "The local backend rejected the opaque cursor",
      );
    }
    throw new NativeFeedDataError(
      `The local Home Feed backend returned HTTP ${response.status}`,
    );
  }
  if (
    response.headers.get("x-reconstruction-data-source") !==
      NATIVE_FEED_DATA_SOURCE ||
    response.headers.get("x-reconstruction-compatibility") !==
      NATIVE_FEED_COMPATIBILITY
  ) {
    throw new NativeFeedDataError(
      "The local backend did not provide the required reconstruction provenance",
    );
  }
  const cacheControl = response.headers.get("cache-control") ?? "";
  if (
    !cacheControl
      .split(",")
      .some(
        (directive) =>
          directive.trim().toLocaleLowerCase("en-US") === "no-store",
      )
  ) {
    throw new NativeFeedDataError(
      "The local backend did not preserve the required no-store boundary",
    );
  }
  const contentType = response.headers.get("content-type") ?? "";
  if (!/^application\/json(?:\s*;|$)/iu.test(contentType)) {
    throw new NativeFeedDataError(
      "The local backend returned a non-JSON response",
    );
  }
  try {
    return await response.json();
  } catch {
    throw new NativeFeedDataError("The local backend returned malformed JSON");
  }
}

function classify(error: unknown): NativeFeedLoadResult {
  const message =
    error instanceof Error ? error.message : "Unknown local feed failure";
  if (message.includes("rejected the opaque cursor")) {
    return { ok: false, reason: "invalid-cursor", message };
  }
  if (message.includes("unavailable") || message.includes("HTTP")) {
    return { ok: false, reason: "unavailable", message };
  }
  return { ok: false, reason: "invalid-response", message };
}

export async function loadNativeFeed(
  kind: NativeFeedKind,
  pageToken?: string,
): Promise<NativeFeedLoadResult> {
  if (!isNativeFeedEnabled()) {
    return {
      ok: false,
      reason: "disabled",
      message: "The local callout preview is not enabled for this server",
    };
  }
  try {
    if (kind !== "ranked" && kind !== "newest") throw new NativeFeedDataError("Unsupported native feed kind");
    validateNativeCursorInput(pageToken, "pageToken");
    const endpoint =
      kind === "newest"
        ? "/services/frontend/home-feed/new"
        : "/services/frontend/home-feed";
    const query = new URLSearchParams({ pageSize: "3" });
    if (pageToken) query.set("pageToken", pageToken);
    const page = validateNativeFeedPage(
      await readLocalJson(`${endpoint}?${query}`),
      kind,
    );
    if (kind !== "newest" || pageToken || !page.headToken) {
      return { ok: true, page };
    }
    const since = page.headToken;
    const count = validateNativeNewCount(
      await readLocalJson(
        `/services/frontend/home-feed/new/count?${new URLSearchParams({ since })}`,
      ),
    );
    return { ok: true, page, count };
  } catch (error) {
    return classify(error);
  }
}
