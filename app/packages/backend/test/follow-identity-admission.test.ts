import test from 'node:test';
import assert from 'node:assert/strict';
import { FollowingStore, type FollowEdge } from '../src/following-store.js';
import { UserStore } from '../src/users-store.js';

for (const field of ['follower_id', 'following_id'] as const) {
  test(`a follow relation requires a usable string ${field}`, () => {
    for (const value of [null, 0, false, {}, [], '']) {
      // These are valid decoded JSON values, but cannot be relation identities.
      const edge = JSON.parse(JSON.stringify({ follower_id: 'a', following_id: 'b', timestamp: 1, [field]: value }));
      assert.throws(() => new FollowingStore(new UserStore([]), [edge as FollowEdge]), /Invalid follow identity/);
    }
  });
}

test('unhydrated nonempty string identities retain their graph facts', () => {
  const store = new FollowingStore(new UserStore([]), [{ follower_id: 'a', following_id: 'b', timestamp: 1 }]);
  assert.equal(store.countFollowers('b'), 1);
  assert.deepEqual(store.relationship('b', 'a'), { user_id: 'a', following_id: 'b', timestamp: 1 });
  assert.deepEqual(store.followersOf('b'), []);
});
