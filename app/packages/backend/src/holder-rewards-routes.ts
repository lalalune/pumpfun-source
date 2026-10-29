import type { FastifyInstance } from "fastify";
import {
  HolderRewardsStore,
  type HolderRewardsSort,
} from "./holder-rewards-store.js";
import { errorBody } from "./users-routes.js";

// Declared exclusive with cursor; any of them selects page mode.
const PAGE_KEYS = ["sort", "direction", "quote", "payingOnly", "page", "limit"];
const SORTS = ["accrued", "lastPayout", "wallets", "trades", "lastTrade"];
// Declared sorts that order by the current quote mark, which a supplied book does not carry.
const MARK_SORTS = ["accruedNow", "distributed"];
// The declared quote filter regex.
const QUOTE = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/;

class HolderRewardsRequestError extends Error {
  constructor(
    readonly statusCode: 400 | 501,
    readonly code: string,
    readonly field: string,
  ) {
    super(code);
  }
}

function integer(
  value: string | undefined,
  field: string,
  maximum: number,
): number | undefined {
  if (value === undefined) return undefined;
  const parsed = Number(value);
  if (
    !/^[1-9][0-9]*$/.test(value) ||
    !Number.isSafeInteger(parsed) ||
    parsed > maximum
  )
    throw new HolderRewardsRequestError(400, "INVALID_QUERY_PARAMETER", field);
  return parsed;
}

/** Website-namespace route, like Home Feed; registered only with an explicit store. */
export function registerHolderRewardsRoutes(
  app: FastifyInstance,
  store: HolderRewardsStore,
): void {
  app.get("/services/frontend/fees/holder-rewards", async (request, reply) => {
    try {
      const query = new Map<string, string>();
      const separator = request.url.indexOf("?");
      for (const [key, value] of new URLSearchParams(
        separator < 0 ? "" : request.url.slice(separator + 1),
      )) {
        if (key !== "cursor" && !PAGE_KEYS.includes(key))
          throw new HolderRewardsRequestError(
            400,
            "UNKNOWN_QUERY_PARAMETER",
            key,
          );
        if (query.has(key))
          throw new HolderRewardsRequestError(
            400,
            "DUPLICATE_QUERY_PARAMETER",
            key,
          );
        query.set(key, value);
      }
      const pageMode = PAGE_KEYS.find((key) => query.has(key));
      if (query.has("cursor") && pageMode)
        throw new HolderRewardsRequestError(
          400,
          "PAGINATION_MODE_CONFLICT",
          pageMode,
        );
      // Cursor mode, including a bare request, orders by accrued.usdAtTrade then usdNow.
      if (!pageMode)
        throw new HolderRewardsRequestError(
          501,
          "CURSOR_MODE_UNAVAILABLE",
          "cursor",
        );
      const sort = query.get("sort");
      if (
        sort !== undefined &&
        !SORTS.includes(sort) &&
        !MARK_SORTS.includes(sort)
      )
        throw new HolderRewardsRequestError(
          400,
          "INVALID_QUERY_PARAMETER",
          "sort",
        );
      const direction = query.get("direction");
      if (
        direction !== undefined &&
        direction !== "asc" &&
        direction !== "desc"
      )
        throw new HolderRewardsRequestError(
          400,
          "INVALID_QUERY_PARAMETER",
          "direction",
        );
      const quote = query.get("quote");
      if (quote !== undefined && !QUOTE.test(quote))
        throw new HolderRewardsRequestError(
          400,
          "INVALID_QUERY_PARAMETER",
          "quote",
        );
      const payingOnly = query.get("payingOnly");
      if (
        payingOnly !== undefined &&
        payingOnly !== "true" &&
        payingOnly !== "false"
      )
        throw new HolderRewardsRequestError(
          400,
          "INVALID_QUERY_PARAMETER",
          "payingOnly",
        );
      const page = integer(query.get("page"), "page", Number.MAX_SAFE_INTEGER);
      const limit = integer(query.get("limit"), "limit", 2000);
      if (
        page !== undefined &&
        !Number.isSafeInteger((page - 1) * (limit ?? 50))
      )
        throw new HolderRewardsRequestError(
          400,
          "INVALID_QUERY_PARAMETER",
          "page",
        );
      // After validation, so a malformed request is still a 400.
      if (sort !== undefined && MARK_SORTS.includes(sort))
        throw new HolderRewardsRequestError(
          501,
          "CURRENT_MARK_SORT_UNAVAILABLE",
          "sort",
        );
      const result = store.page({
        sort: sort as HolderRewardsSort | undefined,
        direction: direction as "asc" | "desc" | undefined,
        quote,
        payingOnly: payingOnly === "true",
        page,
        limit,
      });
      return reply
        .header("X-Reconstruction-Data-Source", store.dataSource)
        .header("X-Reconstruction-Observed-At", store.observedAt)
        .header("X-Reconstruction-Compatibility", "local-unqualified")
        .send(result);
    } catch (error) {
      if (error instanceof HolderRewardsRequestError)
        return reply
          .code(error.statusCode)
          .send(
            error.statusCode === 501
              ? errorBody(501, "COMPATIBILITY_NOT_IMPLEMENTED", {
                  reason: error.code,
                  field: error.field,
                })
              : errorBody(400, error.code, { field: error.field }),
          );
      throw error;
    }
  });
}
