/**
 * Native /following read-operation routes (7 of the 67 documented operations).
 *
 * Registered as native Fastify handlers taking priority over generic fixture
 * replay. Serves deterministic data from the in-memory FollowingStore, whose
 * rows come from the shared UserStore.
 *
 * Parameter handling follows the contract literally, which is stricter than the
 * /users slice: the documented descriptions say out-of-range values are
 * "rejected with 400, not clamped", so this file rejects instead of clamping.
 */
import type { FastifyInstance } from 'fastify';
import { defaultFollowingStore, type FollowingStore } from './following-store.js';
import { errorBody, sendSynthetic, rejectDuplicateQueryKeys, toDeveloperUser, integerLiteral } from './users-routes.js';

const LIST_PAGE = { min: 1, max: 1000, default: 20 } as const;
const SEARCH_PAGE = { min: 1, max: 100, default: 20 } as const;
const SEARCH_TERM_MAX = 50;

interface PageParse {
  limit: number;
  offset: number;
  sort?: 'followers' | 'recent';
}

/** Parse the pagination parameters shared by the two list operations. */
function parseListPage(
  qs: Record<string, string | undefined>,
  bounds: { min: number; max: number; default: number },
): PageParse | string {
  let limit = bounds.default;
  if (qs.limit !== undefined) {
    // Number('') is 0, so an empty or whitespace-only value must not read
    // as a page boundary: it is rejected like any other non-integer, matching
    // the posts and users pagination fix.
    const parsed = integerLiteral(qs.limit);
    if (parsed === null || parsed < bounds.min || parsed > bounds.max) {
      return 'INVALID_LIMIT';
    }
    limit = parsed;
  }
  let offset = 0;
  if (qs.offset !== undefined) {
    // Number('') is 0, so an empty or whitespace-only offset would otherwise
    // silently read as offset 0 and serve the first page with 200.
    const parsed = integerLiteral(qs.offset);
    if (parsed === null || !Number.isSafeInteger(parsed) || parsed < 0) return 'INVALID_OFFSET';
    offset = parsed;
  }
  let sort: 'followers' | 'recent' | undefined;
  if (qs.sort !== undefined) {
    if (qs.sort !== 'followers' && qs.sort !== 'recent') return 'INVALID_SORT';
    sort = qs.sort;
  }
  return { limit, offset, sort };
}

export function registerFollowingRoutes(
  app: FastifyInstance,
  store: FollowingStore = defaultFollowingStore,
): void {
  /**
   * GET /v1/following/single/{id}?userId={viewer}
   * One follow relationship: does `userId` follow `id`?
   * Returns: 200, { follow: FollowRelationship | null }
   */
  app.get('/v1/following/single/:id', async (request, reply) => {
    if (rejectDuplicateQueryKeys(request, reply)) return reply;
    const { id } = request.params as { id: string };
    const qs = request.query as Record<string, string | undefined>;
    const viewer = qs.userId;
    if (viewer === undefined || viewer.length === 0) {
      return reply.code(400).send(errorBody(400, 'INVALID_ID', { parameter: 'userId' }));
    }
    return sendSynthetic(reply, 200, { follow: store.relationship(id, viewer) });
  });

  /**
   * GET /v1/following/v3/followers/count/:userId
   * Returns: 200, { count: number }
   */
  app.get('/v1/following/v3/followers/count/:userId', async (request, reply) => {
    if (rejectDuplicateQueryKeys(request, reply)) return reply;
    const { userId } = request.params as { userId: string };
    return sendSynthetic(reply, 200, { count: store.countFollowers(userId) });
  });

  /**
   * GET /v1/following/v3/following/count/:userId
   * Returns: 200, { count: number }
   */
  app.get('/v1/following/v3/following/count/:userId', async (request, reply) => {
    if (rejectDuplicateQueryKeys(request, reply)) return reply;
    const { userId } = request.params as { userId: string };
    return sendSynthetic(reply, 200, { count: store.countFollowing(userId) });
  });

  /**
   * GET /v1/following/v3/followers/search/:userId?searchTerm=
   * Returns: 200, User[]  — relevance ranked, then paged.
   * Registered before the plain followers page so the literal `search` segment can
   * never be mistaken for a userId.
   */
  app.get('/v1/following/v3/followers/search/:userId', async (request, reply) => {
    if (rejectDuplicateQueryKeys(request, reply)) return reply;
    const { userId } = request.params as { userId: string };
    const qs = request.query as Record<string, string | undefined>;
    const term = qs.searchTerm;
    if (term === undefined || term.length === 0) {
      return reply
        .code(400)
        .send(errorBody(400, 'INVALID_SEARCH_TERM', { parameter: 'searchTerm', reason: 'required' }));
    }
    if ([...term].length > SEARCH_TERM_MAX) {
      return reply.code(400).send(
        errorBody(400, 'INVALID_SEARCH_TERM', {
          parameter: 'searchTerm',
          reason: 'too_long',
          maxLength: SEARCH_TERM_MAX,
          received: [...term].length,
        }),
      );
    }
    const page = parseListPage(qs, SEARCH_PAGE);
    if (typeof page === 'string') {
      return reply.code(400).send(errorBody(400, page));
    }
    const matches = store.searchFollowers(userId, term);
    return sendSynthetic(reply, 200, matches.slice(page.offset, page.offset + page.limit).map(toDeveloperUser));
  });

  /** GET /v1/following/v3/following/search/:userId?searchTerm= — as above. */
  app.get('/v1/following/v3/following/search/:userId', async (request, reply) => {
    if (rejectDuplicateQueryKeys(request, reply)) return reply;
    const { userId } = request.params as { userId: string };
    const qs = request.query as Record<string, string | undefined>;
    const term = qs.searchTerm;
    if (term === undefined || term.length === 0) {
      return reply
        .code(400)
        .send(errorBody(400, 'INVALID_SEARCH_TERM', { parameter: 'searchTerm', reason: 'required' }));
    }
    if ([...term].length > SEARCH_TERM_MAX) {
      return reply.code(400).send(
        errorBody(400, 'INVALID_SEARCH_TERM', {
          parameter: 'searchTerm',
          reason: 'too_long',
          maxLength: SEARCH_TERM_MAX,
          received: [...term].length,
        }),
      );
    }
    const page = parseListPage(qs, SEARCH_PAGE);
    if (typeof page === 'string') {
      return reply.code(400).send(errorBody(400, page));
    }
    const matches = store.searchFollowing(userId, term);
    return sendSynthetic(reply, 200, matches.slice(page.offset, page.offset + page.limit).map(toDeveloperUser));
  });

  /**
   * GET /v1/following/v3/followers/{userId}?limit=&offset=&sort=
   * Returns: 200, User[] — one page.
   */
  app.get('/v1/following/v3/followers/:userId', async (request, reply) => {
    if (rejectDuplicateQueryKeys(request, reply)) return reply;
    const { userId } = request.params as { userId: string };
    const qs = request.query as Record<string, string | undefined>;
    const page = parseListPage(qs, LIST_PAGE);
    if (typeof page === 'string') {
      return reply.code(400).send(errorBody(400, page));
    }
    return sendSynthetic(reply, 200, store.followersOf(userId, page));
  });

  /** GET /v1/following/v3/following/{userId}?limit=&offset=&sort= — as above. */
  app.get('/v1/following/v3/following/:userId', async (request, reply) => {
    if (rejectDuplicateQueryKeys(request, reply)) return reply;
    const { userId } = request.params as { userId: string };
    const qs = request.query as Record<string, string | undefined>;
    const page = parseListPage(qs, LIST_PAGE);
    if (typeof page === 'string') {
      return reply.code(400).send(errorBody(400, page));
    }
    return sendSynthetic(reply, 200, store.followingOf(userId, page));
  });
}
