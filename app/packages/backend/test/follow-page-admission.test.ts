import test from "node:test";
import assert from "node:assert/strict";
import { UserStore, type User } from "../src/users-store.js";
const user = (address: string, userId?: string): User => ({
  address,
  userId,
  username: null,
  profile_image: null,
  bio: null,
  followers: 0,
  following: 0,
  x_username: null,
});
import { FollowingStore } from "../src/following-store.js";
test("direct follow pages obey the declared list bounds", () => {
  const s = new FollowingStore(new UserStore([]), []);
  for (const opts of [
    { offset: NaN },
    { offset: -1 },
    { offset: 1.5 },
    { limit: 0 },
    { limit: 1001 },
    { limit: Infinity },
    { sort: "other" },
  ]) {
    assert.throws(() => s.followersOf("x", opts as any), /page options/);
    assert.throws(() => s.followingOf("x", opts as any), /page options/);
  }
  assert.deepEqual(s.followersOf("x", { offset: 0, limit: 1000 }), []);
});
