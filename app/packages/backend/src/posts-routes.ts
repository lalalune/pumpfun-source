/**
 * Native /posts read-operation routes.
 *
 * Registered as native Fastify handlers taking priority over the generic fixture-replay loop.
 * Serves deterministic data from the in-memory PostStore linked to UserStore.
 */
import type { FastifyInstance } from 'fastify';
import { PostStore, defaultPostStore } from './posts-store.js';
import { sendSynthetic, errorBody, rejectDuplicateQueryKeys, integerLiteral } from './users-routes.js';

const POST_ID = /^([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}|00000000-0000-0000-0000-000000000000|ffffffff-ffff-ffff-ffff-ffffffffffff)$/;

/**
 * Pagination on the posts sub-resources is declared as integers in
 * contracts/developer.openapi.json (limit minimum 1, offset minimum 0, both
 * with maximum 9007199254740991; likers/reposters offset maximum 10000).
 * The previous parsing silently truncated fractional values and silently
 * fell back to the default for non-numeric or non-finite values, so
 * limit=1.5 served one row and limit=abc served the default page, both
 * with 200. A supplied value must parse to a safe integer; an empty or
 * whitespace-only value is not an integer literal either (Number('') is 0,
 * so it would otherwise read as limit=0 / offset=0). Out-of-range
 * safe integers keep the existing clamp behavior (limit capped at 200,
 * offset at 10000, negative offset at 0, as the existing negative-offset
 * test documents). Returns null for an invalid supplied value.
 */
function pageValue(
  qs: Record<string, string | undefined>,
  field: string,
  fallback: number,
  minimum: number,
  maximum: number,
): number | null {
  const raw = qs[field];
  if (raw === undefined) return fallback;
  const parsed = integerLiteral(raw);
  if (parsed === null || !Number.isSafeInteger(parsed)) return null;
  return Math.min(maximum, Math.max(minimum, parsed));
}

export function registerPostRoutes(app: FastifyInstance, store: PostStore = defaultPostStore): void {
  /**
   * GET /v1/posts
   * Fetch posts by ids (comma-separated or repeated query parameters).
   * Request order is preserved; duplicates collapse; unknown, hidden or deleted ids leave no placeholder.
   * Returns: 200, { posts: Post[] }
   */
  app.get('/v1/posts', async (request, reply) => {
    const qs = request.query as Record<string, unknown>;
    const rawIds = qs.ids;
    if (!rawIds) {
      return reply.code(400).send(errorBody(400, 'IDS_REQUIRED'));
    }

    const list: string[] = [];
    if (typeof rawIds === 'string') {
      list.push(...rawIds.split(',').map(s => s.trim()).filter(Boolean));
    } else if (Array.isArray(rawIds)) {
      for (const item of rawIds) {
        if (typeof item === 'string') {
          list.push(...item.split(',').map(s => s.trim()).filter(Boolean));
        }
      }
    }

    if (list.length === 0) {
      return reply.code(400).send(errorBody(400, 'IDS_REQUIRED'));
    }

    // Contract specifies maxItems: 100 on ids array
    if (list.length > 100) {
      return reply.code(400).send(errorBody(400, 'TOO_MANY_IDS', { maxItems: 100, received: list.length }));
    }

    if (list.some(id => !POST_ID.test(id))) {
      return reply.code(400).send(errorBody(400, 'INVALID_POST_ID'));
    }

    const posts = store.batch(list);
    return sendSynthetic(reply, 200, { posts });
  });

  /**
   * GET /v1/posts/:postId/replies
   * Direct live replies to a post, newest first, keyset-paginated on an opaque cursor.
   * Returns: 200, { replies: Post[], nextCursor: string | null }
   * NOTE: Registered before /v1/posts/:postId to prevent route shadowing.
   */
  app.get('/v1/posts/:postId/replies', async (request, reply) => {
    if (rejectDuplicateQueryKeys(request, reply)) return reply;
    const { postId } = request.params as { postId: string };
    const qs = request.query as Record<string, string | undefined>;

    const limit = pageValue(qs, 'limit', 50, 1, 200);
    if (limit === null) {
      return reply.code(400).send(errorBody(400, 'INVALID_LIMIT'));
    }

    try {
      const result = store.getReplies(postId, { cursor: qs.cursor, limit });
      if (!result) {
        return reply.code(404).send(errorBody(404, 'NOT_FOUND'));
      }
      return sendSynthetic(reply, 200, result);
    } catch (err: unknown) {
      if (err instanceof Error && err.message === 'INVALID_CURSOR') {
        return reply.code(400).send(errorBody(400, 'INVALID_CURSOR'));
      }
      throw err;
    }
  });

  /**
   * GET /v1/posts/:postId/likers
   * Profiles who liked a post, newest first, offset-paginated.
   * Returns: 200, { likers: Profile[], hasMore: boolean }
   * NOTE: Registered before /v1/posts/:postId.
   */
  app.get('/v1/posts/:postId/likers', async (request, reply) => {
    if (rejectDuplicateQueryKeys(request, reply)) return reply;
    const { postId } = request.params as { postId: string };
    const qs = request.query as Record<string, string | undefined>;

    const limit = pageValue(qs, 'limit', 50, 1, 200);
    if (limit === null) {
      return reply.code(400).send(errorBody(400, 'INVALID_LIMIT'));
    }

    const offset = pageValue(qs, 'offset', 0, 0, 10000);
    if (offset === null) {
      return reply.code(400).send(errorBody(400, 'INVALID_OFFSET'));
    }

    const result = store.getLikers(postId, { limit, offset });
    if (!result) {
      return reply.code(404).send(errorBody(404, 'NOT_FOUND'));
    }
    return sendSynthetic(reply, 200, result);
  });

  /**
   * GET /v1/posts/:postId/quotes
   * Live quotes of a post, newest first, keyset-paginated on an opaque cursor.
   * Returns: 200, { quotes: Post[], nextCursor: string | null }
   * NOTE: Registered before /v1/posts/:postId.
   */
  app.get('/v1/posts/:postId/quotes', async (request, reply) => {
    if (rejectDuplicateQueryKeys(request, reply)) return reply;
    const { postId } = request.params as { postId: string };
    const qs = request.query as Record<string, string | undefined>;

    const limit = pageValue(qs, 'limit', 50, 1, 200);
    if (limit === null) {
      return reply.code(400).send(errorBody(400, 'INVALID_LIMIT'));
    }

    try {
      const result = store.getQuotes(postId, { cursor: qs.cursor, limit });
      if (!result) {
        return reply.code(404).send(errorBody(404, 'NOT_FOUND'));
      }
      return sendSynthetic(reply, 200, result);
    } catch (err: unknown) {
      if (err instanceof Error && err.message === 'INVALID_CURSOR') {
        return reply.code(400).send(errorBody(400, 'INVALID_CURSOR'));
      }
      throw err;
    }
  });

  /**
   * GET /v1/posts/:postId/reposters
   * Profiles who plain-reposted a post, newest first, offset-paginated.
   * Returns: 200, { reposters: Profile[], hasMore: boolean }
   * NOTE: Registered before /v1/posts/:postId.
   */
  app.get('/v1/posts/:postId/reposters', async (request, reply) => {
    if (rejectDuplicateQueryKeys(request, reply)) return reply;
    const { postId } = request.params as { postId: string };
    const qs = request.query as Record<string, string | undefined>;

    const limit = pageValue(qs, 'limit', 50, 1, 200);
    if (limit === null) {
      return reply.code(400).send(errorBody(400, 'INVALID_LIMIT'));
    }

    const offset = pageValue(qs, 'offset', 0, 0, 10000);
    if (offset === null) {
      return reply.code(400).send(errorBody(400, 'INVALID_OFFSET'));
    }

    const result = store.getReposters(postId, { limit, offset });
    if (!result) {
      return reply.code(404).send(errorBody(404, 'NOT_FOUND'));
    }
    return sendSynthetic(reply, 200, result);
  });

  /**
   * GET /v1/posts/:postId
   * Fetch a single post with its one-level embeds.
   * Returns: 200 with { post: Post }, or 404 for unknown, hidden or deleted posts.
   */
  app.get('/v1/posts/:postId', async (request, reply) => {
    // The single-post read takes no query parameters, but a repeated key is
    // still ambiguous input: fail closed like the sub-resources and the
    // /users reads instead of silently serving past it.
    if (rejectDuplicateQueryKeys(request, reply)) return reply;
    const { postId } = request.params as { postId: string };
    const post = store.getLivePost(postId);
    if (!post) {
      return reply.code(404).send(errorBody(404, 'NOT_FOUND'));
    }
    return sendSynthetic(reply, 200, { post });
  });
}
