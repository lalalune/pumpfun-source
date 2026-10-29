import { CALLOUT_DISCUSSIONS_NATIVE_ROUTES, registerCalloutDiscussionRoutes } from "./callout-discussions-routes.js";
import type { CalloutDiscussionsStore } from "./callout-discussions-store.js";
import Fastify from "fastify";
import { CALLOUTS_NATIVE_ROUTES, registerCalloutRoutes } from "./callouts-routes.js";
import type { CalloutsStore } from "./callouts-store.js";
import { PositionsStore } from "./positions-store.js";
import { registerPositionsRoutes, POSITIONS_NATIVE_ROUTES } from "./positions-routes.js";
import type { PayoutsStore } from "./payouts-store.js";
import { registerPayoutRoutes, PAYOUTS_NATIVE_ROUTES } from "./payouts-routes.js";
import type { UserTradesStore } from "./user-trades-store.js";
import { registerUserTradesRoutes, USER_TRADES_NATIVE_ROUTES } from "./user-trades-routes.js";
import { apiKeyGate } from "./api-key-gate.js";
import { registerSearchResolveRoutes, SEARCH_RESOLVE_NATIVE_ROUTES } from "./search-resolve-routes.js";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { validateHeaderName, validateHeaderValue } from "node:http";
import { fileURLToPath } from "node:url";
import { registerPostRoutes } from "./posts-routes.js";
import { PostStore, defaultPostStore } from "./posts-store.js";
import { registerUserRoutes } from "./users-routes.js";
import { UserStore, defaultStore } from "./users-store.js";
import { registerCompetitionRoutes } from "./competitions-routes.js";
import { CompetitionStore, defaultCompetitionStore } from "./competitions-store.js";
import { registerFollowingRoutes } from "./following-routes.js";
import { FollowingStore, defaultFollowingStore } from "./following-store.js";
import { registerLeaderboardRoutes } from "./leaderboard-routes.js";
import { LeaderboardStore, defaultLeaderboardStore } from "./leaderboard-store.js";
import { registerHomeFeedRoutes } from "./home-feed-routes.js";
import { HomeFeedStore, defaultHomeFeedStore } from "./home-feed-store.js";
import { registerLocalMediaRoutes, type LocalMediaOptions } from "./local-media-routes.js";
import type { PortfolioBalancesStore } from "./portfolio-balances-store.js";
import { registerPortfolioBalancesRoutes, PORTFOLIO_BALANCES_NATIVE_ROUTES } from "./portfolio-balances-routes.js";

export type Fixture = {
  method: string;
  path: string;
  query?: Record<string, string>;
  status: number;
  headers?: Record<string, string>;
  body: unknown;
  source: string;
};

const reservedFixturePaths = new Set([
  "/health",
  "/__reconstruction/status",
  "/__reconstruction/openapi.json",
  "/services/frontend/home-feed",
  "/services/frontend/home-feed/new",
  "/services/frontend/home-feed/new/count",
]);

function compareKeys([left]: [string, string], [right]: [string, string]) {
  return left === right ? 0 : left < right ? -1 : 1;
}

export function fixtureKey(
  method: string,
  path: string,
  query: Record<string, string> = {},
) {
  const parameters = new URLSearchParams(
    Object.entries(query).sort(compareKeys),
  );
  return `${method.toUpperCase()} ${path}?${parameters.toString()}`;
}

function fixtureProvenance(fixture: unknown, index: number) {
  const source =
    fixture && typeof fixture === "object"
      ? (fixture as { source?: unknown }).source
      : undefined;
  if (typeof source !== "string" || source.length === 0) {
    return `fixture[${index}] source=<missing>`;
  }
  const digest = createHash("sha256").update(source).digest("hex").slice(0, 12);
  return `fixture[${index}] sourceSha256=${digest}`;
}

function isJsonBody(value: unknown, ancestors = new Set<object>()): boolean {
  if (value === null || typeof value === "string" || typeof value === "boolean") return true;
  if (typeof value === "number") return Number.isFinite(value);
  if (typeof value !== "object" || ancestors.has(value)) return false;
  if (!Array.isArray(value) && ![Object.prototype, null].includes(Object.getPrototypeOf(value))) return false;
  ancestors.add(value);
  try {
    // Array iteration visits holes as undefined, unlike Array.every.
    const children = Array.isArray(value) ? value : Object.values(value);
    for (const child of children) if (!isJsonBody(child, ancestors)) return false;
    return true;
  } finally { ancestors.delete(value); }
}

function validateFixture(
  fixture: unknown,
  index: number,
): asserts fixture is Fixture {
  const provenance = fixtureProvenance(fixture, index);
  if (!fixture || typeof fixture !== "object" || Array.isArray(fixture)) {
    throw new Error(
      `Invalid fixture registration (${provenance}): expected an object`,
    );
  }
  const candidate = fixture as Partial<Record<keyof Fixture, unknown>>;
  if (!Object.hasOwn(candidate, "body") || candidate.body === undefined) {
    throw new Error(
      `Invalid fixture registration (${provenance}): body must be explicitly present; use null for a JSON null body`,
    );
  }
  if (!Buffer.isBuffer(candidate.body) && !isJsonBody(candidate.body)) {
    throw new Error(`Invalid fixture registration (${provenance}): body must contain finite JSON values or a raw Buffer`);
  }
  if (typeof candidate.source !== "string" || candidate.source.length === 0) {
    throw new Error(
      `Invalid fixture registration (${provenance}): source must be a non-empty string`,
    );
  }
  if (typeof candidate.method !== "string" || candidate.method.length === 0) {
    throw new Error(
      `Invalid fixture registration (${provenance}): method must be a non-empty string`,
    );
  }
  if (!["GET", "HEAD"].includes(candidate.method.toUpperCase())) {
    throw new Error(
      `Invalid fixture registration (${provenance}): only GET and HEAD are supported`,
    );
  }
  if (
    typeof candidate.path !== "string" ||
    !candidate.path.startsWith("/") ||
    candidate.path.startsWith("//") ||
    candidate.path.includes("?") ||
    candidate.path.includes("#")
  ) {
    throw new Error(
      `Invalid fixture registration (${provenance}): path must be a local absolute path without a query or fragment`,
    );
  }
  try {
    if (/[^\x21-\x7e]/.test(candidate.path)) throw new URIError();
    decodeURI(candidate.path);
  } catch {
    throw new Error(
      `Invalid fixture registration (${provenance}): path must be a valid percent-encoded ASCII request-target`,
    );
  }
  if (candidate.query !== undefined) {
    if (
      candidate.query === null ||
      typeof candidate.query !== "object" ||
      Array.isArray(candidate.query) ||
      Object.getPrototypeOf(candidate.query) !== Object.prototype
    ) {
      throw new Error(
        `Invalid fixture registration (${provenance}): query must be a plain object`,
      );
    }
    if (
      Object.values(candidate.query).some((value) => typeof value !== "string")
    ) {
      throw new Error(
        `Invalid fixture registration (${provenance}): query values must be strings`,
      );
    }
    try {
      for (const [name, value] of Object.entries(candidate.query)) {
        // URLSearchParams replaces unpaired surrogates; reject lossy keys first.
        encodeURIComponent(name);
        encodeURIComponent(value as string);
      }
    } catch {
      throw new Error(
        `Invalid fixture registration (${provenance}): query keys and values must be well-formed Unicode`,
      );
    }
  }
  if (
    typeof candidate.status !== "number" ||
    !Number.isInteger(candidate.status) ||
    candidate.status < 200 ||
    candidate.status > 599
  ) {
    throw new Error(
      `Invalid fixture registration (${provenance}): status must be an integer from 200 through 599`,
    );
  }
  const status = candidate.status as number;
  if (
    candidate.body !== null &&
    (status === 204 || status === 205 || status === 304)
  ) {
    throw new Error(
      `Invalid fixture registration (${provenance}): status ${status} responses cannot carry a body; use null`,
    );
  }
  if (candidate.headers !== undefined) {
    if (
      candidate.headers === null ||
      typeof candidate.headers !== "object" ||
      Array.isArray(candidate.headers) ||
      Object.getPrototypeOf(candidate.headers) !== Object.prototype
    ) {
      throw new Error(
        `Invalid fixture registration (${provenance}): headers must be a plain object`,
      );
    }
    const headerNames = new Set<string>();
    for (const [name, value] of Object.entries(candidate.headers)) {
      try {
        validateHeaderName(name);
      } catch {
        throw new Error(
          `Invalid fixture registration (${provenance}): headers contain an invalid HTTP field name`,
        );
      }
      const canonicalName = name.toLowerCase();
      if (headerNames.has(canonicalName)) {
        throw new Error(
          `Invalid fixture registration (${provenance}): headers contain duplicate case-insensitive HTTP field names`,
        );
      }
      headerNames.add(canonicalName);
      if (typeof value !== "string") {
        throw new Error(
          `Invalid fixture registration (${provenance}): header values must be strings`,
        );
      }
      try {
        validateHeaderValue(name, value);
      } catch {
        throw new Error(
          `Invalid fixture registration (${provenance}): headers contain an invalid HTTP field value`,
        );
      }
    }
  }
}

function registerFixtures(fixtures: Fixture[]) {
  if (!Array.isArray(fixtures)) {
    throw new Error("Invalid fixture registration: expected an array");
  }
  const fixtureMap = new Map<string, Fixture>();
  const provenanceByKey = new Map<string, string>();
  for (const [index, fixture] of fixtures.entries()) {
    validateFixture(fixture, index);
    const provenance = fixtureProvenance(fixture, index);
    if (reservedFixturePaths.has(fixture.path)) {
      const pathDigest = createHash("sha256")
        .update(fixture.path)
        .digest("hex")
        .slice(0, 12);
      throw new Error(
        `Reserved fixture route pathSha256=${pathDigest}: ${provenance}`,
      );
    }
    const key = fixtureKey(fixture.method, fixture.path, fixture.query);
    const previous = provenanceByKey.get(key);
    if (previous) {
      const keyDigest = createHash("sha256")
        .update(key)
        .digest("hex")
        .slice(0, 12);
      throw new Error(
        `Duplicate canonical fixture key keySha256=${keyDigest}: ${previous}; ${provenance}`,
      );
    }
    const snapshot = structuredClone(fixture);
    // structuredClone turns a Buffer into Uint8Array; preserve raw replay bodies.
    if (Buffer.isBuffer(fixture.body)) snapshot.body = Buffer.from(fixture.body);
    fixtureMap.set(key, snapshot);
    provenanceByKey.set(key, provenance);
  }
  return fixtureMap;
}

/**
 * Routes handled natively and therefore excluded from the generic replay loop.
 * Key: `METHOD /openapi-path` (the OpenAPI template path, not the Fastify param path).
 */
const NATIVE_ROUTES = new Set<string>([
  "GET /users",
  "GET /users/{id}",
  "POST /users/batch",
  "GET /users/username-exists/{username}",
  "GET /users/search-v2",
  "GET /users/{id}/overview",
  "POST /profiles/verified",
  "GET /profiles/verified",
  "GET /posts",
  "GET /posts/{postId}",
  "GET /posts/{postId}/replies",
  "GET /posts/{postId}/likers",
  "GET /posts/{postId}/quotes",
  "GET /posts/{postId}/reposters",
  "GET /competitions",
  "GET /competitions/{idOrSlug}",
  "GET /competitions/{id}/entries/{entryId}",
  "GET /competitions/{id}/entries/{entryId}/highlights",
  "GET /competitions/{id}/highlights",
  "GET /following/single/{id}",
  "GET /following/v3/followers/count/{userId}",
  "GET /following/v3/following/count/{userId}",
  "GET /following/v3/followers/search/{userId}",
  "GET /following/v3/following/search/{userId}",
  "GET /following/v3/followers/{userId}",
  "GET /following/v3/following/{userId}",
  "GET /pnl-leaderboard",
]);

export interface BuildAppOptions {
  /** Explicit server-owned public callout materialization; absent retains fixture/501 behavior. */
  calloutsStore?: CalloutsStore;
  calloutDiscussionsStore?: CalloutDiscussionsStore;
  /** Explicit local materialization; absent preserves the fixture/501 harness. */
  positionsStore?: PositionsStore;
  /** Explicit confirmed-payout facts; absent preserves fixture/501 behavior. */
  payoutsStore?: PayoutsStore;
  /** Explicit operator-owned spot trade history; absent retains fixture/501 behavior. */
  userTradesStore?: UserTradesStore;
  /** Explicit local/CLI-only capability; absent by default, independent of developer auth. */
  localMedia?: LocalMediaOptions;
  /** Override the user store (for tests). */
  userStore?: UserStore;
  /** Override the post store (for tests). */
  postStore?: PostStore;
  /** Override the competition store (for tests). */
  competitionStore?: CompetitionStore;
  /** Override the follow-graph store (for tests). */
  followingStore?: FollowingStore;
  /** Override the leaderboard store (for tests). */
  leaderboardStore?: LeaderboardStore;
  /** Explicit server-owned public aggregate balance snapshot, disabled by default. */
  portfolioBalancesStore?: PortfolioBalancesStore;
  /** Override the local Home Feed store (for tests). */
  homeFeedStore?: HomeFeedStore;
}

/**
 * Read the developer specification served verbatim at
 * /__reconstruction/openapi.json and hashed at /__reconstruction/status.
 * A lossy "utf8" read would silently replace a corrupted byte with U+FFFD:
 * the JSON still parses when the byte sits inside a string value, so the app
 * would start serving altered specification text while reporting a hash of
 * the altered text rather than the file. Decode fatally so a malformed
 * specification fails app construction instead, like the startup loaders in
 * server.ts.
 */
export function readSpecificationText(specPath: string): string {
  return new TextDecoder("utf-8", { fatal: true }).decode(
    readFileSync(specPath),
  );
}

export function buildApp(fixtures: Fixture[] = [], opts: BuildAppOptions = {}) {
  // Reject an invalid inventory before constructing an application that can listen.
  const fixtureMap = registerFixtures(fixtures);
  const app = Fastify({ logger: false });
  const specPath = fileURLToPath(
    new URL("../../../contracts/developer.openapi.json", import.meta.url),
  );
  const specification = readSpecificationText(specPath);
  const spec = JSON.parse(specification) as {
    paths: Record<string, Record<string, unknown>>;
  };
  app.get("/health", async () => ({
    status: "ok",
    mode: "reconstruction",
    compatibility: "unqualified",
  }));
  app.get("/__reconstruction/openapi.json", async (_, reply) =>
    reply.type("application/json").send(specification),
  );
  app.get("/__reconstruction/status", async () => ({
    fixtureCount: fixtureMap.size,
    specificationSha256: createHash("sha256")
      .update(specification)
      .digest("hex"),
    compatibility: "unqualified",
  }));
  if (opts.localMedia) {
    const { store } = opts.localMedia;
    app.addHook("onClose", async () => { await store.close(); });
    registerLocalMediaRoutes(app, opts.localMedia);
  }
  // Register native handlers first. They win over a captured fixture for the same route.
  // They are documented /v1 operations too, so the same API-key gate runs before them.
  const store = opts.userStore ?? defaultStore;
  const postStore =
    opts.postStore ?? (opts.userStore ? new PostStore(undefined, store) : defaultPostStore);
  const compStore =
    opts.competitionStore ??
    (opts.userStore ? new CompetitionStore(undefined, store) : defaultCompetitionStore);
  const followStore =
    opts.followingStore ??
    (opts.userStore ? new FollowingStore(store) : defaultFollowingStore);
  const lbStore =
    opts.leaderboardStore ??
    (opts.userStore ? new LeaderboardStore(undefined, store) : defaultLeaderboardStore);
  registerHomeFeedRoutes(app, opts.homeFeedStore ?? defaultHomeFeedStore);
  app.register(async (native) => {
    native.addHook("preHandler", apiKeyGate);
    if (opts.portfolioBalancesStore) registerPortfolioBalancesRoutes(native, opts.portfolioBalancesStore);
    registerUserRoutes(native, store);
    if (opts.userStore) registerSearchResolveRoutes(native, store);
    registerPostRoutes(native, postStore);
    registerCompetitionRoutes(native, compStore);
    registerFollowingRoutes(native, followStore);
    registerLeaderboardRoutes(native, lbStore);
    if (opts.calloutsStore) registerCalloutRoutes(native, opts.calloutsStore);
    if (opts.calloutDiscussionsStore) registerCalloutDiscussionRoutes(native, opts.calloutDiscussionsStore);
    if (opts.positionsStore) registerPositionsRoutes(native, opts.positionsStore);
    if (opts.payoutsStore) registerPayoutRoutes(native, opts.payoutsStore);
    if (opts.userTradesStore) registerUserTradesRoutes(native, opts.userTradesStore);
  });

  // Routing recognizes documented paths; no fabricated domain responses or live proxy fallback.
  for (const [path, item] of Object.entries(spec.paths)) {
    for (const method of Object.keys(item).filter((value) =>
      ["get", "post", "put", "patch", "delete", "head", "options"].includes(
        value,
      ),
    )) {
      // Skip operations that a native handler already serves.
      if (NATIVE_ROUTES.has(`${method.toUpperCase()} ${path}`) ||
        (opts.userStore && SEARCH_RESOLVE_NATIVE_ROUTES.has(`${method.toUpperCase()} ${path}`)) ||
        (opts.portfolioBalancesStore && PORTFOLIO_BALANCES_NATIVE_ROUTES.has(`${method.toUpperCase()} ${path}`)) ||
        (opts.calloutDiscussionsStore && CALLOUT_DISCUSSIONS_NATIVE_ROUTES.has(`${method.toUpperCase()} ${path}`)) ||
        (opts.calloutsStore && CALLOUTS_NATIVE_ROUTES.has(`${method.toUpperCase()} ${path}`)) ||
        (opts.positionsStore && POSITIONS_NATIVE_ROUTES.has(`${method.toUpperCase()} ${path}`)) ||
        (opts.payoutsStore && PAYOUTS_NATIVE_ROUTES.has(`${method.toUpperCase()} ${path}`)) ||
        (opts.userTradesStore && USER_TRADES_NATIVE_ROUTES.has(`${method.toUpperCase()} ${path}`))) continue;
      app.route({
        method: method.toUpperCase() as "GET",
        url: "/v1" + path.replace(/\{([^}]+)\}/g, ":$1"),
        // Every documented operation declares the global bearer requirement;
        // the gate runs before replay so a fixture cannot bypass it.
        preHandler: apiKeyGate,
        handler: replay,
      });
    }
  }
  app.all("/*", replay);

  function replay(request: { method: string; url: string }, reply: any) {
    // URL normalizes dot segments; fixture paths must match the raw request target.
    const separator = request.url.indexOf("?");
    const pathname =
      separator < 0 ? request.url : request.url.slice(0, separator);
    const entries = [
      ...new URLSearchParams(
        separator < 0 ? "" : request.url.slice(separator + 1),
      ).entries(),
    ];
    // The fixture format cannot represent duplicate query keys: fail explicitly.
    if (new Set(entries.map(([key]) => key)).size !== entries.length) {
      return reply
        .code(501)
        .send({ error: "DUPLICATE_QUERY_KEYS_UNIMPLEMENTED" });
    }
    const fixture = fixtureMap.get(
      fixtureKey(request.method, pathname, Object.fromEntries(entries)),
    );
    if (!fixture) {
      return reply.code(501).send({
        error: "COMPATIBILITY_NOT_IMPLEMENTED",
        method: request.method,
        path: pathname,
      });
    }
    if (fixture.headers) reply.headers(fixture.headers);
    // RFC 9110 section 15.3.6 forbids content in a 205 response.
    if (fixture.status === 205) return reply.code(205).send();
    // Fixture bodies are JSON by default; explicit non-JSON types stay verbatim.
    const contentType = reply.getHeader("content-type");
    if (
      (fixture.body === null || typeof fixture.body === "string") &&
      (contentType === undefined ||
        (typeof contentType === "string" &&
          /^application\/(?:[^;\s]+\+)?json(?:\s*;|$)/i.test(contentType)))
    ) {
      if (contentType === undefined) reply.type("application/json");
      return reply.code(fixture.status).send(JSON.stringify(fixture.body));
    }
    return reply.code(fixture.status).send(fixture.body);
  }

  return app;
}
