import test from 'node:test';
import assert from 'node:assert/strict';
import { PostStore, SYNTHETIC_POSTS_SEED } from '../src/posts-store.js';

const root = SYNTHETIC_POSTS_SEED.find(post => post.kind === 'root' && !post.hidden && !post.deleted)!;
const reply = SYNTHETIC_POSTS_SEED.find(post => post.parentPostId === root.postId && !post.hidden && !post.deleted)!;
const quote = SYNTHETIC_POSTS_SEED.find(post => post.quotedPostId === root.postId && post.kind === 'quote' && !post.hidden && !post.deleted)!;
const id = (index: number) => `00000000-0000-4000-8000-${String(index).padStart(12, '0')}`;
const rows = [root, ...Array.from({length: 205}, (_, index) => ({...reply, postId: id(index + 10000)})),
  ...Array.from({length: 205}, (_, index) => ({...quote, postId: id(index + 20000)}))];

test('direct keyset reads keep the documented 1..200 limit clamp', () => {
  const store = new PostStore(rows);
  const pages = [
    (limit?: number) => store.getReplies(root.postId, { limit })!.replies,
    (limit?: number) => store.getQuotes(root.postId, { limit })!.quotes,
  ];
  for (const page of pages) {
    assert.equal(page(-1).length, 1);
    assert.equal(page(0).length, 1);
    assert.equal(page(1000).length, 200);
    assert.equal(page().length, 50);
  }
});

test('all direct post-page methods reject unsafe or fractional numeric inputs', () => {
  const store = new PostStore(rows);
  for (const value of [NaN, Infinity, -Infinity, 1.5, Number.MAX_SAFE_INTEGER + 1]) {
    for (const method of ['getReplies', 'getQuotes', 'getLikers', 'getReposters'] as const) {
      assert.throws(() => store[method](root.postId, { limit: value }), /Invalid post pagination/);
    }
    for (const method of ['getLikers', 'getReposters'] as const) {
      assert.throws(() => store[method](root.postId, { offset: value }), /Invalid post pagination/);
    }
  }
});

test('a direct clamped reply page retains a consumable continuation', () => {
  const store = new PostStore(rows);
  const first = store.getReplies(root.postId, { limit: 0 })!;
  assert.equal(first.replies.length, 1);
  assert.ok(first.nextCursor);
  const second = store.getReplies(root.postId, { limit: 0, cursor: first.nextCursor })!;
  assert.equal(second.replies.length, 1);
  assert.notEqual(second.replies[0].postId, first.replies[0].postId);
});
