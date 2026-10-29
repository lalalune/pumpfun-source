/**
 * Integer query values must be plain decimal literals.
 *
 * Number() accepts hex/binary/octal prefixes, exponents, surrounding
 * whitespace, a leading '+' and leading zeros, so limit=0x10 read as 16 and
 * limit=1e1 as 10 on the users, posts, pnl-leaderboard, following and
 * competitions routes, all with 200. The payouts, positions, callouts and
 * user-trades routes already reject these spellings.
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildApp } from './with-api-key.js';

const NON_DECIMAL = ['0x10', '0b1', '0o7', '1e1', '2.0', '01', '+2', ' 2', '2 '];

const POST = '/v1/posts/00000000-0000-4000-8000-000000000001';
const COMPETITION = '/v1/competitions/11111111-1111-4000-8000-000000000002';
const cases: [route: string, fields: string[]][] = [
  ['/v1/users', ['offset', 'limit']],
  ['/v1/users/search-v2', ['offset', 'limit']],
  [`${POST}/replies`, ['limit']],
  [`${POST}/likers`, ['limit', 'offset']],
  ['/v1/pnl-leaderboard?period=daily', ['limit', 'positionsLimit']],
  ['/v1/following/v3/followers/user-001', ['limit', 'offset']],
  ['/v1/following/v3/following/search/user-001?searchTerm=al', ['limit', 'offset']],
  [COMPETITION, ['limit', 'positionsLimit']],
  [`${COMPETITION}/highlights`, ['limit', 'perMemberLimit']],
  [`${COMPETITION}/entries/22222222-2222-4000-8000-000000000001/highlights`, ['limit']],
];

test('non-decimal integer spellings are rejected with 400', async (t) => {
  const app = buildApp([]);
  t.after(() => app.close());
  for (const [route, fields] of cases) {
    const separator = route.includes('?') ? '&' : '?';
    for (const field of fields) {
      for (const value of NON_DECIMAL) {
        const response = await app.inject(`${route}${separator}${field}=${encodeURIComponent(value)}`);
        assert.equal(response.statusCode, 400, `${route} ${field}=${JSON.stringify(value)}`);
      }
    }
  }
});

test('plain decimal values, including negative clamping, are still served', async (t) => {
  const app = buildApp([]);
  t.after(() => app.close());
  for (const url of [
    '/v1/users?offset=0&limit=2',
    `${POST}/likers?limit=2&offset=-5`,
    '/v1/pnl-leaderboard?period=daily&limit=2',
    '/v1/following/v3/followers/user-001?limit=2&offset=0',
    `${COMPETITION}?limit=0&positionsLimit=99`,
  ]) {
    const response = await app.inject(url);
    assert.equal(response.statusCode, 200, url);
  }
});
