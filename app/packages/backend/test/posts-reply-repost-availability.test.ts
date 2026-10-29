import test from 'node:test';
import assert from 'node:assert/strict';
import { PostStore, SYNTHETIC_POSTS_SEED } from '../src/posts-store.js';
import { buildApp } from './with-api-key.js';

const root = SYNTHETIC_POSTS_SEED.find(post => post.kind === 'root' && !post.hidden && !post.deleted)!;
const repost = SYNTHETIC_POSTS_SEED.find(post => post.kind === 'repost' && !post.hidden && !post.deleted)!;
const unavailable = [null, '00000000-0000-4000-8000-000000000998',
  SYNTHETIC_POSTS_SEED.find(post => post.deleted)!.postId,
  SYNTHETIC_POSTS_SEED.find(post => post.hidden)!.postId];

test('reply pages apply the same served-repost boundary as single and batch reads', async () => {
  const children = unavailable.map((repostedPostId, index) => ({ ...repost,
    postId: `00000000-0000-4000-8000-${String(5000 + index).padStart(12, '0')}`,
    parentPostId: root.postId, rootPostId: root.postId, repostedPostId,
    createdAt: '2030-01-01T00:00:00.000Z',
  }));
  const store = new PostStore([...SYNTHETIC_POSTS_SEED, ...children]);
  for (const child of children) assert.equal(store.getLivePost(child.postId), undefined);
  assert.deepEqual(store.batch(children.map(child => child.postId)), []);
  const app = buildApp([], { postStore: store });
  try {
    let cursor: string | null = null;
    const seen: string[] = [];
    do {
      const response = await app.inject({ method: 'GET', url: `/v1/posts/${root.postId}/replies?limit=1${cursor ? '&cursor=' + cursor : ''}` });
      assert.equal(response.statusCode, 200);
      const page = response.json();
      assert.equal(page.replies.length, 1);
      for (const post of page.replies) {
        assert.ok(!children.some(child => child.postId === post.postId));
        assert.ok(!seen.includes(post.postId));
        seen.push(post.postId);
      }
      cursor = page.nextCursor;
    } while (cursor);
    const expected = SYNTHETIC_POSTS_SEED.filter(post => post.parentPostId === root.postId && !post.deleted && !post.hidden).map(post => post.postId);
    assert.deepEqual(seen.sort(), expected.sort());
  } finally { await app.close(); }
});
