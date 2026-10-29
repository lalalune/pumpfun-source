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
test("follow epochs cannot corrupt sorting or serialize as null", () => {
  for (const timestamp of [NaN, Infinity, -1, 1.5, Number.MAX_SAFE_INTEGER + 1])
    assert.throws(
      () =>
        new FollowingStore(new UserStore([]), [
          { follower_id: "a", following_id: "b", timestamp },
        ]),
      /timestamp/,
    );
  assert.doesNotThrow(
    () =>
      new FollowingStore(new UserStore([]), [
        { follower_id: "a", following_id: "b", timestamp: 0 },
      ]),
  );
});
