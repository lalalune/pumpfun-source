import assert from "node:assert/strict";
import test from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { ProfileHeader } from "../src/components/profile/ProfileHeader";
import { FeedItem } from "../src/components/feed/FeedItem";
import type { LocalProfile } from "../src/components/profile/profile-data";
import type { LocalFeedPost } from "../src/components/feed/feed-data";

const profile: LocalProfile = {
  address: "",
  userId: "synthetic-walletless",
  displayName: "Synthetic group",
  username: "Synthetic group",
  bio: null,
  kind: "group",
  memberCount: 2,
  followers: 0,
  following: 0,
  banned: false,
  isPumpUser: false,
  xUsername: null,
  hasRecordedAvatar: false,
  posts: [],
  dataSource: "synthetic-seed-play",
};

test("walletless header discloses absent wallet and renders no empty clipboard control", () => {
  const html = renderToStaticMarkup(createElement(ProfileHeader, { profile }));
  assert.match(html, /Synthetic group/);
  assert.match(html, /No wallet address recorded/);
  assert.doesNotMatch(html, /Copy wallet address|Copy address|<code><\/code>/);
  assert.match(html, /Synthetic identity/);
  assert.match(
    html,
    /disabled=""[^>]*title="Authentication and follow writes are unavailable offline"/,
  );
  const walletHtml = renderToStaticMarkup(
    createElement(ProfileHeader, {
      profile: { ...profile, address: "synthetic-wallet-address" },
    }),
  );
  assert.match(walletHtml, /Copy wallet address/);
  assert.match(walletHtml, /synthetic-wallet-address/);
  assert.doesNotMatch(walletHtml, /No wallet address recorded/);
});

test("walletless post markup is distinct from an unresolved author", () => {
  const item: LocalFeedPost = {
    id: "synthetic-post",
    author: { address: "", name: "Synthetic group", missing: false },
    content: "Synthetic text",
    timestamp: "2024-01-01T00:00:00.000Z",
    timestampLabel: "Jan 1, 2024",
    likes: 0,
    replies: 0,
    reposts: 0,
    quotes: 0,
    hasMedia: false,
    dataSource: "synthetic-seed-play",
  };
  const html = renderToStaticMarkup(createElement(FeedItem, { item }));
  assert.match(html, /No wallet address recorded/);
  assert.doesNotMatch(html, /Unresolved seed identity/);
  assert.match(html, /Synthetic example/);
  const unresolved = renderToStaticMarkup(
    createElement(FeedItem, {
      item: { ...item, author: { ...item.author, missing: true } },
    }),
  );
  assert.match(unresolved, /Unresolved seed identity/);
  assert.doesNotMatch(unresolved, /No wallet address recorded/);
});

test("feed author links use exact known profile identities and keep unknown authors plain", () => {
  const item: LocalFeedPost = {
    id: "author-link",
    author: {
      address: "wallet-one",
      userId: "user-one",
      name: "Local author",
      missing: false,
    },
    content: "Local example",
    timestamp: "2024-01-01T00:00:00.000Z",
    timestampLabel: "Jan 1, 2024",
    likes: 0,
    replies: 0,
    reposts: 0,
    quotes: 0,
    hasMedia: false,
    dataSource: "synthetic-seed-play",
  };
  const render = (author: LocalFeedPost["author"]) =>
    renderToStaticMarkup(
      createElement(FeedItem, { item: { ...item, author } }),
    );
  const wallet = render(item.author);
  assert.match(wallet, /href="\/profile\/wallet-one"/);
  assert.doesNotMatch(wallet, /href="\/profile\/user-one"/);
  assert.match(wallet, /Synthetic example/);
  assert.match(wallet, /class="feed-avatar" aria-hidden="true">L<\/div>/);

  // Walletless identities retain their exact id; they are not normalized into addresses.
  assert.match(
    render({ ...item.author, address: "", userId: "group:one" }),
    /href="\/profile\/group%3Aone"/,
  );
  assert.match(
    render({ ...item.author, address: " invalid-wallet", userId: "usable-id" }),
    /href="\/profile\/usable-id"/,
  );
  for (const author of [
    { ...item.author, missing: true },
    { ...item.author, address: "", userId: undefined },
    { ...item.author, address: "invalid/address", userId: " invalid-id" },
    { ...item.author, address: "", userId: "a".repeat(129) },
  ]) {
    const html = render(author);
    assert.doesNotMatch(html, /<a[ >]/);
    assert.match(html, /Local author/);
    assert.match(html, /Synthetic example/);
  }
});
