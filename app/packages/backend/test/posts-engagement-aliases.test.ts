import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { PostStore, type RawPost } from '../src/posts-store.js';
import { UserStore, type User } from '../src/users-store.js';
import { buildApp } from './with-api-key.js';

const users = JSON.parse(readFileSync(new URL('../src/users-seed.json', import.meta.url), 'utf8')) as User[];
const posts = JSON.parse(readFileSync(new URL('../src/posts-seed.json', import.meta.url), 'utf8')) as RawPost[];

for (const kind of ['likers', 'reposters'] as const) {
  test(`${kind} paginate resolved accounts once across wallet and user-ID aliases`, async () => {
    const row = structuredClone(posts[0]);
    row[kind] = ['missing-user', users[1].address, users[1].userId!, users[1].address, users[0].userId!, users[0].address];
    const userStore = new UserStore(users);
    const app = buildApp([], {userStore, postStore: new PostStore([row], userStore)});
    try {
      for (const [offset, ids, hasMore] of [
        [0, [users[1].userId], true],
        [1, [users[0].userId], false],
        [2, [], false],
      ] as const) {
        const response = await app.inject(`/v1/posts/${row.postId}/${kind}?limit=1&offset=${offset}`);
        assert.equal(response.statusCode, 200);
        const body = response.json();
        assert.deepEqual(body[kind].map((user: {userId: string}) => user.userId), ids);
        assert.equal(body.hasMore, hasMore);
      }
      const complete = await app.inject(`/v1/posts/${row.postId}/${kind}`);
      assert.deepEqual(complete.json()[kind].map((user: {userId: string}) => user.userId), [users[1].userId, users[0].userId]);
      assert.equal(complete.json()[kind][1].isVerified, true);
      assert.equal(complete.json().hasMore, false);
    } finally { await app.close(); }
  });

  test(`${kind} preserve distinct default account order and hidden-post behavior`, async () => {
    const row = structuredClone(posts[0]);
    const userStore = new UserStore(users);
    const app = buildApp([], {userStore, postStore: new PostStore([row], userStore)});
    try {
      const response = await app.inject(`/v1/posts/${row.postId}/${kind}`);
      assert.equal(response.statusCode, 200);
      assert.deepEqual(response.json()[kind].map((user: {userId: string}) => user.userId), row[kind]);
    } finally { await app.close(); }
    row.hidden = true;
    const hiddenApp = buildApp([], {userStore, postStore: new PostStore([row], userStore)});
    try {
      assert.equal((await hiddenApp.inject(`/v1/posts/${row.postId}/${kind}`)).statusCode, 404);
    } finally { await hiddenApp.close(); }
  });
}
