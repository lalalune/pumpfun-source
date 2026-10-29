import type { FastifyInstance } from 'fastify';
import type { operations } from './generated/developer-api.js';
import type { UserStore } from './users-store.js';
import { errorBody, sendSynthetic, toDeveloperUser } from './users-routes.js';

type Resolution = operations['get_search_resolve']['responses'][200]['content']['application/json'];
// Local UUID-only boundary reuses the posts shapes (including nil/max); not an upstream validator.
const ACCOUNT_ID = /^([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}|00000000-0000-0000-0000-000000000000|ffffffff-ffff-ffff-ffff-ffffffffffff)$/;
export const SEARCH_RESOLVE_NATIVE_ROUTES = new Set(['GET /search/resolve']);

/** Known local account IDs only; no coin/address registry or upstream absence inference. */
export function registerSearchResolveRoutes(app: FastifyInstance, store: UserStore): void {
  app.get('/v1/search/resolve', async (request, reply) => {
    const separator = request.url.indexOf('?');
    const query = new URLSearchParams(separator < 0 ? '' : request.url.slice(separator + 1));
    if ([...query.keys()].some(key => key !== 'identifiers')) {
      return reply.code(501).send(errorBody(501, 'COMPATIBILITY_NOT_IMPLEMENTED', {
        reason: 'SEARCH_RESOLVE_QUERY_UNSUPPORTED',
      }));
    }
    // Repeated and mixed comma forms are explicitly equivalent. Do not trim,
    // normalize or deduplicate: each identifier is echoed verbatim in request order.
    const identifiers = query.getAll('identifiers').flatMap(value => value.split(','));
    if (identifiers.length < 1 || identifiers.length > 5 || identifiers.some(id => id.length > 128)) {
      return reply.code(400).send(errorBody(400, 'INVALID_QUERY'));
    }
    const results: Resolution['results'] = [];
    for (const identifier of identifiers) {
      const user = ACCOUNT_ID.test(identifier) ? store.getById(identifier) : undefined;
      if (!user || user.userId !== identifier) {
        // A missing account, address or unsupported shape requires another adapter.
        // Never label it unknown/external_wallet or return a partial successful batch.
        return reply.code(501).send(errorBody(501, 'COMPATIBILITY_NOT_IMPLEMENTED', {
          reason: 'SEARCH_RESOLVE_IDENTIFIER_UNAVAILABLE',
        }));
      }
      const isGroup = user.kind === 'group';
      results.push({
        identifier,
        kind: isGroup ? 'squad' : 'user',
        chain: null,
        coin: null,
        user: toDeveloperUser(user),
        resolvedVia: isGroup ? 'group' : 'cc_user',
        definitive: true,
      });
    }
    // Definitive within this supplied local account model, never a production verdict.
    reply.header('Cache-Control', 'no-store').header('X-Reconstruction-Compatibility', 'unqualified');
    return sendSynthetic(reply, 200, { results, degraded: [] } satisfies Resolution);
  });
}
