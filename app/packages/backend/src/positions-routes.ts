import type { FastifyInstance, FastifyReply } from "fastify";
import {
  AmbiguousPositionError,
  UnavailableUpdatesError,
  PositionsStore,
  type PortfolioOptions,
} from "./positions-store.js";

export const POSITIONS_NATIVE_ROUTES = new Set([
  "GET /user-positions/{userId}",
  "GET /user-portfolio/{userId}",
]);
class QueryError extends Error {}
function query(url: string, allowed: string[]): Map<string, string> {
  const result = new Map<string, string>();
  for (const [key, value] of new URLSearchParams(
    url.includes("?") ? url.slice(url.indexOf("?") + 1) : "",
  )) {
    if (!allowed.includes(key) || result.has(key)) throw new QueryError();
    result.set(key, value);
  }
  return result;
}
function integer(
  value: string | undefined,
  minimum: number,
  maximum: number,
): number | undefined {
  if (value === undefined) return undefined;
  if (!/^-?(?:0|[1-9]\d*)$/.test(value)) throw new QueryError();
  const number = Number(value);
  if (!Number.isSafeInteger(number) || number < minimum || number > maximum)
    throw new QueryError();
  return number;
}
function boolean(value: string | undefined): boolean | undefined {
  if (value === undefined) return undefined;
  if (value === "true" || value === "1") return true;
  if (value === "false" || value === "0") return false;
  throw new QueryError();
}
function choice<T extends string>(
  value: string | undefined,
  values: T[],
): T | undefined {
  if (value === undefined) return undefined;
  const normalized = value.trim().toUpperCase();
  if (!values.includes(normalized as T)) throw new QueryError();
  return normalized as T;
}
function failure(error: unknown, reply: FastifyReply) {
  if (error instanceof QueryError || error instanceof RangeError)
    return reply.code(400).send({ statusCode: 400, error: "INVALID_QUERY" });
  if (error instanceof UnavailableUpdatesError)
    return reply
      .code(501)
      .send({
        statusCode: 501,
        error: "COMPATIBILITY_NOT_IMPLEMENTED",
        reason: "CALLOUT_UPDATES_UNAVAILABLE",
      });
  if (error instanceof AmbiguousPositionError)
    return reply
      .code(501)
      .send({
        statusCode: 501,
        error: "COMPATIBILITY_NOT_IMPLEMENTED",
        reason: "AMBIGUOUS_MINT_CHAIN",
      });
  throw error;
}
function send(reply: FastifyReply, store: PositionsStore, result: unknown) {
  if (result === null)
    return reply.code(404).send({ statusCode: 404, error: "NOT_FOUND" });
  return reply
    .header("X-Reconstruction-Data-Source", store.dataSource)
    .header("X-Reconstruction-Observed-At", store.observedAt)
    .header("X-Reconstruction-Compatibility", "unqualified")
    .send(result);
}

/** Registered inside the existing developer API-key gate; never a website alias. */
export function registerPositionsRoutes(
  app: FastifyInstance,
  store: PositionsStore,
): void {
  app.get("/v1/user-positions/:userId", async (request, reply) => {
    try {
      const qs = query(request.url, ["mints", "updatesLimit"]);
      if (!qs.has("mints")) throw new QueryError();
      const mints = qs.get("mints")!.split(",");
      if (mints.length > 200) throw new QueryError();
      const limit = integer(qs.get("updatesLimit"), 0, 20);
      if (mints.some((mint) => mint.startsWith("hlcore:")))
        return reply
          .code(501)
          .send({
            statusCode: 501,
            error: "COMPATIBILITY_NOT_IMPLEMENTED",
            reason: "PERPETUAL_POSITIONS_DEFERRED",
          });
      return send(
        reply,
        store,
        store.positions(
          (request.params as { userId: string }).userId,
          mints,
          limit,
        ),
      );
    } catch (error) {
      return failure(error, reply);
    }
  });
  app.get("/v1/user-portfolio/:userId", async (request, reply) => {
    try {
      const qs = query(request.url, [
        "filter",
        "sortBy",
        "page",
        "pageSize",
        "chainId",
        "totalsOnly",
        "filterSpam",
        "spamOnly",
      ]);
      const opts: PortfolioOptions = {
        filter: choice(qs.get("filter"), ["OPEN", "CLOSED", "ALL"]),
        sortBy: choice(qs.get("sortBy"), ["PNL", "POSITION_SIZE", "RECENCY"]),
        page: integer(qs.get("page"), 0, Number.MAX_SAFE_INTEGER),
        pageSize: integer(qs.get("pageSize"), 1, 200),
        chainId: integer(
          qs.get("chainId"),
          Number.MIN_SAFE_INTEGER,
          Number.MAX_SAFE_INTEGER,
        ),
        totalsOnly: boolean(qs.get("totalsOnly")),
        filterSpam: boolean(qs.get("filterSpam")),
        spamOnly: boolean(qs.get("spamOnly")),
      };
      return send(
        reply,
        store,
        store.portfolio((request.params as { userId: string }).userId, opts),
      );
    } catch (error) {
      return failure(error, reply);
    }
  });
}
