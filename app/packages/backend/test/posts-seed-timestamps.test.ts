import test from 'node:test';
import assert from 'node:assert/strict';
import { PostStore, SYNTHETIC_POSTS_SEED } from '../src/posts-store.js';

const root = SYNTHETIC_POSTS_SEED.find(post => post.kind === 'root' && !post.deleted && !post.hidden)!;

test('invalid post dates cannot enter the keyset comparator', () => {
  for (const createdAt of ['', 'invalid-date']) {
    assert.throws(() => new PostStore([{ ...root, createdAt }]), /Invalid post timestamp/);
  }
});

test('unknown dates and existing parseable date representations remain unchanged', () => {
  for (const createdAt of [null, root.createdAt, '2024-01-01T12:00:00+02:00']) {
    const store = new PostStore([{ ...root, createdAt }]);
    assert.equal(store.getLivePost(root.postId)!.createdAt, createdAt);
  }
});

test('a returned reply cursor can be consumed for every accepted timestamp', () => {
  const replies = SYNTHETIC_POSTS_SEED.filter(post => post.parentPostId === root.postId && !post.deleted && !post.hidden).slice(0, 2);
  assert.equal(replies.length, 2);
  for (const createdAt of [null, replies[0].createdAt]) {
    const store = new PostStore([root, { ...replies[0], createdAt }, replies[1]]);
    const first = store.getReplies(root.postId, { limit: 1 })!;
    assert.ok(first.nextCursor);
    const second = store.getReplies(root.postId, { limit: 1, cursor: first.nextCursor })!;
    assert.equal(second.replies.length, 1);
    assert.notEqual(second.replies[0].postId, first.replies[0].postId);
    assert.equal(second.nextCursor, null);
  }
});
