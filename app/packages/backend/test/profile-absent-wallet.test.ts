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
import { userToProfile } from "../src/posts-store.js";
test("walletless shared profiles carry null rather than an empty wallet", () => {
  assert.equal(userToProfile(user("", "local-id"), false).walletAddress, null);
  assert.equal(
    userToProfile(user("wallet", "local-id"), false).walletAddress,
    "wallet",
  );
});
