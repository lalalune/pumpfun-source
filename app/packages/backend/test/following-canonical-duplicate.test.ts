import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import { UserStore, type User } from '../src/users-store.js';
import { FollowingStore } from '../src/following-store.js';
import { buildApp } from '../src/app.js';

const seed = (): User[] => JSON.parse(readFileSync(new URL('../src/users-seed.json', import.meta.url), 'utf8'));
test('canonical follower/following pairs cannot be repeated through account aliases', () => {
  const users = seed(), store = new UserStore(users), [a, b] = users;
  for (const edges of [
    [{ follower_id: a.userId!, following_id: b.userId!, timestamp: 1 },
      { follower_id: a.address, following_id: b.userId!, timestamp: 2 }],
    [{ follower_id: a.userId!, following_id: b.userId!, timestamp: 1 },
      { follower_id: a.userId!, following_id: b.address, timestamp: 2 }],
  ]) assert.throws(() => new FollowingStore(store, edges), /Duplicate follow relation/);
});
test('distinct canonical relations retain consistent HTTP counts and pages', async () => {
  const users = seed(), store = new UserStore(users), [a, b, c] = users;
  const follows = new FollowingStore(store, [
    { follower_id: a.address, following_id: b.userId!, timestamp: 1 },
    { follower_id: c.userId!, following_id: b.userId!, timestamp: 2 },
  ]);
  const app = buildApp([], { userStore: store, followingStore: follows });
  const headers = { authorization: `Bearer pf_live_${'A'.repeat(49)}` };
  try {
    const count = await app.inject({url: `/v1/following/v3/followers/count/${b.userId}`, headers});
    const page = await app.inject({url: `/v1/following/v3/followers/${b.userId}`, headers});
    assert.equal(count.statusCode, 200); assert.equal(page.statusCode, 200);
    assert.equal(count.json().count, 2);
    assert.equal(new Set(page.json().map((row: {userId: string}) => row.userId)).size, 2);
  } finally { await app.close(); }
});
