import { test } from "node:test";
import assert from "node:assert/strict";
import {
  findSettings,
  SETTINGS_DEFINITIONS,
} from "../packages/frontend/src/components/settings/settings-model";
test("mapped identifier words participate in existing term-AND search", () => {
  for (const [query, id] of [
    ["privacy confirmExternalLinks", "privacy.confirmExternalLinks"],
    ["notifications browserPush", "notifications.browserPush"],
  ])
    assert.deepEqual(
      findSettings(query).map((item) => item.id),
      [id],
    );
});
test("identifier text composes with existing metadata without widening the catalog", () => {
  assert.deepEqual(
    findSettings("privacy confirmExternalLinks warning").map((item) => item.id),
    ["privacy.confirmExternalLinks"],
  );
  const before = JSON.stringify(SETTINGS_DEFINITIONS);
  findSettings("browserPush");
  assert.equal(JSON.stringify(SETTINGS_DEFINITIONS), before);
});
test("empty, unknown and literal dotted queries retain existing behavior", () => {
  for (const query of [
    "",
    "not-mapped-setting",
    "privacy.confirmExternalLinks",
  ])
    assert.deepEqual(findSettings(query), []);
  assert.deepEqual(
    findSettings("GróUP CHATS").map((item) => item.id),
    ["chat.allowGroupNotifications"],
  );
});
