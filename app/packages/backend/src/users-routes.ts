/**
 * Native /users read-operation routes.
 *
 * These are registered as native Fastify handlers and take priority over the
 * generic fixture-replay catch-all.  They serve deterministic data from the
 * in-memory UserStore.
 */
import type { FastifyInstance, FastifyReply } from 'fastify';
import { UserStore, defaultStore, DATA_SOURCE, type User } from './users-store.js';

/**
 * Response marker for hand-authored synthetic data.
 *
 * app/AGENTS.md forbids fabricated domain responses, so every successful native
 * response states plainly that its payload is synthetic seed data and not captured
 * evidence. Error responses carry no marker because they contain no domain data.
 */
export const SYNTHETIC_HEADER = 'X-Reconstruction-Data-Source';

export function sendSynthetic(reply: FastifyReply, code: number, body: unknown) {
  return reply.code(code).header(SYNTHETIC_HEADER, DATA_SOURCE).send(body);
}

/**
 * Error bodies follow the documented `Error` component
 * (components.schemas.Error), whose only always-present field is statusCode.
 * Route-specific detail is additive; the envelope stays conformant.
 */
export function errorBody(statusCode: number, error: string, extra: Record<string, unknown> = {}) {
  return { statusCode, error, ...extra };
}

/**
 * The shared profile schema permits last_active_at for signed-in website reads,
 * but explicitly says it is absent on the developer API host. An API key is not
 * a website viewer. Project without changing the underlying domain-store row.
 */
export function toDeveloperUser(user: User): Omit<User, 'last_active_at'> {
  const { last_active_at: _activity, ...profile } = user;
  return profile;
}

/** Hydrated search and batch rows omit the single-profile rename timestamp. */
function toHydratedDeveloperUser(user: User): Omit<User, 'last_active_at' | 'last_username_update_timestamp'> {
  const { last_username_update_timestamp: _renamed, ...profile } = toDeveloperUser(user);
  return profile;
}

/**
 * Keep the existing replay harness's fail-closed duplicate-query boundary on
 * native reads too. The scalar OpenAPI parameters do not establish semantics
 * for repeated keys; selecting a value or coercing an array would invent them.
 * Decode key names so `searchTerm` and `%73earchTerm` cannot bypass the check.
 */
export function rejectDuplicateQueryKeys(request: { url: string }, reply: FastifyReply): boolean {
  const separator = request.url.indexOf('?');
  if (separator < 0) return false;
  const keys = new Set<string>();
  for (const key of new URLSearchParams(request.url.slice(separator + 1)).keys()) {
    if (keys.has(key)) {
      reply.code(501).send({ error: 'DUPLICATE_QUERY_KEYS_UNIMPLEMENTED' });
      return true;
    }
    keys.add(key);
  }
  return false;
}

/**
 * Both user read contracts bound offset/limit to JavaScript safe integers.
 * An empty or whitespace-only value is not an integer literal (Number('') is
 * 0, so it would otherwise read as offset=0 / limit=0) and is rejected like
 * any other non-integer, matching /v1/pnl-leaderboard.
 */
function userPageValue(raw: string | undefined): number | null | undefined {
  if (raw === undefined) return undefined;
  if (raw.trim() === '') return null;
  const parsed = Number(raw);
  return Number.isSafeInteger(parsed) ? parsed : null;
}

function userPagination(qs: Record<string, string | undefined>) {
  const offset = userPageValue(qs.offset);
  const limit = userPageValue(qs.limit);
  if (offset === null || limit === null) return null;
  return { offset, limit };
}

export function registerUserRoutes(app: FastifyInstance, store: UserStore = defaultStore): void {
  /**
   * GET /v1/users
   * List users with optional sort, order, offset, limit.
   * Returns: 200, JSON array of User.
   */
  app.get('/v1/users', async (request, reply) => {
    if (rejectDuplicateQueryKeys(request, reply)) return reply;
    const qs = request.query as Record<string, string | undefined>;
    // Contract permits any safe integer for offset/limit (including negatives).
    // Documented assumption: negatives clamp to 0 rather than producing
    // slicing surprises, so offset<0 behaves as 0 and limit<0 returns [].
    const pagination = userPagination(qs);
    if (!pagination) return reply.code(400).send(errorBody(400, 'INVALID_QUERY'));
    const { offset, limit } = pagination;
    const result = store.list({
      sort: qs.sort,
      order: qs.order,
      offset: offset === undefined ? undefined : Math.max(0, offset),
      limit: limit === undefined ? undefined : Math.max(0, limit),
    });
    return sendSynthetic(reply, 200, result.map(toDeveloperUser));
  });

  /**
   * GET /v1/users/search-v2
   * Search users with query filters, sorting, and pagination.
   * Returns: 200, JSON array of User.
   *
   * NOTE: This must be registered BEFORE /v1/users/:id so that
   * "search-v2" is not captured as `:id`.
   */
  app.get('/v1/users/search-v2', async (request, reply) => {
    if (rejectDuplicateQueryKeys(request, reply)) return reply;
    const qs = request.query as Record<string, string | undefined>;
    const pagination = userPagination(qs);
    if (!pagination) return reply.code(400).send(errorBody(400, 'INVALID_QUERY'));
    const { offset, limit } = pagination;
    // includeLabelledWallets is a boolean in the contract, but any value other
    // than 'true'/'1' previously read as false, so a typo or garbage value
    // silently narrowed the result set instead of failing. The sibling
    // boolean parsers reject anything else: positions boolean() throws on
    // anything but true/1/false/0, home-feed boolean() on anything but
    // true/false, and this file's own batch handler rejects a non-boolean
    // forceFetch. Accept the same true/1/false/0 spellings positions does.
    let includeLabelledWallets = false;
    if (qs.includeLabelledWallets !== undefined) {
      if (qs.includeLabelledWallets === 'true' || qs.includeLabelledWallets === '1') {
        includeLabelledWallets = true;
      } else if (qs.includeLabelledWallets === 'false' || qs.includeLabelledWallets === '0') {
        includeLabelledWallets = false;
      } else {
        return reply.code(400).send(errorBody(400, 'INVALID_QUERY'));
      }
    }
    const result = store.search({
      searchTerm: qs.searchTerm,
      sort: qs.sort,
      order: qs.order,
      offset: offset === undefined ? undefined : Math.max(0, offset),
      limit: limit === undefined ? undefined : Math.max(0, limit),
      includeLabelledWallets,
    });
    return sendSynthetic(reply, 200, result.map(user => user.wallet_label?.trim() ? toDeveloperUser(user) : toHydratedDeveloperUser(user)));
  });

  /**
   * GET /v1/users/username-exists/:username
   * Check if a username is taken.
   * Returns: 200, { exists_flag: boolean }.
   *
   * NOTE: This must be registered BEFORE /v1/users/:id so that
   * "username-exists" is not captured as `:id`.
   */
  app.get('/v1/users/username-exists/:username', async (request, reply) => {
    if (rejectDuplicateQueryKeys(request, reply)) return reply;
    const { username } = request.params as { username: string };
    return sendSynthetic(reply, 200, { exists_flag: store.usernameExists(username) });
  });

  /**
   * POST /v1/users/batch
   * Fetch users by addresses.
   * Request body: { addresses: string[], forceFetch?: boolean }
   * Returns: 201, JSON array of User.
   *
   * NOTE: This must be registered BEFORE /v1/users/:id.
   */
  app.post('/v1/users/batch', async (request, reply) => {
    if (rejectDuplicateQueryKeys(request, reply)) return reply;
    const body = request.body as { addresses?: string[]; forceFetch?: boolean } | null;
    if (!body || !Array.isArray(body.addresses)) {
      return reply.code(400).send(errorBody(400, 'ADDRESSES_REQUIRED'));
    }
    // Contract declares maxItems: 100 on addresses. Reject rather than silently truncate.
    if (body.addresses.length > 100) {
      return reply.code(400).send(errorBody(400, 'TOO_MANY_ADDRESSES', { maxItems: 100, received: body.addresses.length }));
    }
    if (body.addresses.some(address => typeof address !== 'string')) {
      return reply.code(400).send(errorBody(400, 'INVALID_ADDRESS'));
    }
    if (body.forceFetch !== undefined && typeof body.forceFetch !== 'boolean') {
      return reply.code(400).send(errorBody(400, 'INVALID_FORCE_FETCH'));
    }
    const result = store.batch(body.addresses);
    return sendSynthetic(reply, 201, result.map(toHydratedDeveloperUser));
  });

  /**
   * GET /v1/users/:id/overview
   * Get an overview of a user account.
   * Returns: 200 with UserOverview, or 404 with error body.
   *
   * NOTE: This must be registered BEFORE /v1/users/:id.
   */
  app.get('/v1/users/:id/overview', async (request, reply) => {
    if (rejectDuplicateQueryKeys(request, reply)) return reply;
    const { id } = request.params as { id: string };
    const overview = store.getOverview(id);
    if (!overview) {
      return reply.code(404).send(errorBody(404, 'NOT_FOUND'));
    }
    if (overview.degraded.length > 0) reply.header('Cache-Control', 'no-store');
    return sendSynthetic(reply, 200, {
      ...overview,
      profile: overview.profile === null ? null : toDeveloperUser(overview.profile),
    });
  });

  /**
   * GET /v1/users/:id
   * Get a user by wallet address or userId.
   * Returns: 200 with User, or 404 with error body.
   *
   * Contract does not specify a 404 response, so this is a documented assumption:
   * we return 404 with { error: "NOT_FOUND" } when no user matches.
   */
  app.get('/v1/users/:id', async (request, reply) => {
    if (rejectDuplicateQueryKeys(request, reply)) return reply;
    const { id } = request.params as { id: string };
    const user = store.getById(id);
    if (!user) {
      return reply.code(404).send(errorBody(404, 'NOT_FOUND'));
    }
    return sendSynthetic(reply, 200, toDeveloperUser(user));
  });

  /**
   * POST /v1/profiles/verified
   * Check verified status for a list of wallets or user ids.
   * Request body: { ids: string[] }
   * Returns: 201, object mapping each requested id to boolean.
   */
  app.post('/v1/profiles/verified', async (request, reply) => {
    if (rejectDuplicateQueryKeys(request, reply)) return reply;
    const body = request.body as { ids?: unknown } | null;
    if (!body || typeof body !== 'object' || !Array.isArray(body.ids)) {
      return reply.code(400).send(errorBody(400, 'IDS_REQUIRED'));
    }
    // Contract declares minItems: 1
    if (body.ids.length === 0) {
      return reply.code(400).send(errorBody(400, 'EMPTY_IDS', { minItems: 1, received: 0 }));
    }
    // Contract declares maxItems: 200
    if (body.ids.length > 200) {
      return reply.code(400).send(errorBody(400, 'TOO_MANY_IDS', { maxItems: 200, received: body.ids.length }));
    }
    // Contract declares items: type string, maxLength: 64
    for (const id of body.ids) {
      if (typeof id !== 'string' || [...id].length > 64) {
        return reply.code(400).send(errorBody(400, 'INVALID_ID', { maxLength: 64, received: id }));
      }
    }
    const result = store.batchVerified(body.ids as string[]);
    return sendSynthetic(reply, 201, result);
  });
}
