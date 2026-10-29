/**
 * Native /pnl-leaderboard read-operation route.
 *
 * Registered as a native Fastify handler taking priority over generic fixture
 * replay. Serves deterministic synthetic data from LeaderboardStore, with
 * profile fields hydrated from the shared UserStore.
 */
import type { FastifyInstance } from 'fastify';
import {
  LeaderboardStore,
  UnavailableLeaderProfilesError,
  defaultLeaderboardStore,
  isPeriod,
  isSort,
} from './leaderboard-store.js';
import { sendSynthetic, errorBody, rejectDuplicateQueryKeys, integerLiteral } from './users-routes.js';

/**
 * Pagination on the PnL board is declared as integers in
 * contracts/developer.openapi.json (`limit` rows served, default and ceiling
 * 100; `positionsLimit` top positions per row, default 3, values above 5 clamp
 * to 5). The previous parsing silently truncated fractional values and silently
 * fell back to the default for non-numeric or non-finite values, so
 * limit=1.5 served one row and limit=abc served the default board, both
 * with 200. A supplied value must parse to a safe integer; an empty or
 * whitespace-only value is not an integer literal either. Out-of-range safe
 * integers keep the existing store clamp behavior. Returns null for an
 * invalid supplied value.
 */
function pageValue(
  raw: string | undefined,
): number | null | undefined {
  if (raw === undefined) return undefined;
  const parsed = integerLiteral(raw);
  if (parsed === null || !Number.isSafeInteger(parsed)) return null;
  return parsed;
}

export function registerLeaderboardRoutes(
  app: FastifyInstance,
  store: LeaderboardStore = defaultLeaderboardStore,
): void {
  // Despite its name, this GET returns daily leaders, not a verified-badge filter.
  // It shares the existing developer API-key gate and synthetic-data attribution.
  app.get('/v1/profiles/verified', async (request, reply) => {
    if (rejectDuplicateQueryKeys(request, reply)) return reply;
    try {
      return sendSynthetic(reply, 200, store.getDailyLeaderProfiles());
    } catch (error) {
      if (error instanceof UnavailableLeaderProfilesError) {
        return reply.code(501).send(errorBody(501, 'COMPATIBILITY_NOT_IMPLEMENTED', {
          reason: 'DAILY_LEADER_PROFILES_UNAVAILABLE',
        }));
      }
      throw error;
    }
  });

  /**
   * GET /v1/pnl-leaderboard
   * The PnL board for a required period window, ranked by the chosen measure
   * (combined by default), descending.
   * Returns: 200, { entries, periodType, periodLabel, windowStartSec }.
   *
   * `period` is a required enum; a missing or unknown value is a 400 rather than
   * a silent default. A missing `sort`, `positionsLimit` or `limit` defaults
   * leniently, matching the other native routes, but a supplied pagination
   * value must be a safe integer (see pageValue above). A repeated query key
   * (including a percent-encoded one) fails closed with 501
   * DUPLICATE_QUERY_KEYS_UNIMPLEMENTED, like the other native reads, before
   * any value is interpreted.
   */
  app.get('/v1/pnl-leaderboard', async (request, reply) => {
    if (rejectDuplicateQueryKeys(request, reply)) return reply;
    const qs = request.query as Record<string, string | undefined>;

    if (qs.period === undefined) {
      return reply.code(400).send(errorBody(400, 'PERIOD_REQUIRED', {
        allowed: ['daily', 'weekly', 'monthly'],
      }));
    }
    if (!isPeriod(qs.period)) {
      return reply.code(400).send(errorBody(400, 'INVALID_PERIOD', {
        allowed: ['daily', 'weekly', 'monthly'],
        received: qs.period,
      }));
    }

    const limit = pageValue(qs.limit);
    if (limit === null) {
      return reply.code(400).send(errorBody(400, 'INVALID_LIMIT'));
    }
    const positionsLimit = pageValue(qs.positionsLimit);
    if (positionsLimit === null) {
      return reply.code(400).send(errorBody(400, 'INVALID_POSITIONS_LIMIT'));
    }

    const board = store.getBoard({
      period: qs.period,
      // An unknown sort falls back to the default measure instead of failing.
      sort: isSort(qs.sort) ? qs.sort : undefined,
      positionsLimit,
      limit,
    });

    return sendSynthetic(reply, 200, board);
  });
}
