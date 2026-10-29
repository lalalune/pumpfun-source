import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  SETTINGS_DEFINITIONS,
  SETTINGS_SECTIONS,
  findSettings,
  readSettingsLocation,
  settingsHref,
} from "../packages/frontend/src/components/settings/settings-model.ts";

test("all public captured sections can be selected; privileged admin is unavailable", () => {
  for (const { id } of SETTINGS_SECTIONS) {
    assert.equal(
      readSettingsLocation(new URLSearchParams({ settings: id })).section,
      id,
    );
  }
  assert.equal(
    readSettingsLocation(new URLSearchParams("settings=admin")).section,
    null,
  );
});

test("malformed, duplicate, unknown and absent sections fail closed", () => {
  for (const query of [
    "",
    "settings",
    "settings=",
    "settings=nope",
    "settings=Notifications",
    "settings=notifications&settings=privacy",
    "settings=notifications&settings=notifications",
    "settings=%3Cscript%3E",
    "setting=display.language",
  ]) {
    assert.deepEqual(readSettingsLocation(new URLSearchParams(query)), {
      section: null,
      settingId: null,
    });
  }
});

test("focus targets must be known and belong to the selected section", () => {
  assert.deepEqual(
    readSettingsLocation(
      new URLSearchParams("settings=display&setting=display.language"),
    ),
    { section: "display", settingId: "display.language" },
  );
  for (const target of [
    "unknown",
    "__proto__",
    "privacy.confirmExternalLinks",
    "display.language&setting=display.language",
  ]) {
    assert.equal(
      readSettingsLocation(
        new URLSearchParams(`settings=display&setting=${target}`),
      ).settingId,
      null,
    );
  }
});

test("close removes all owned keys and preserves unrelated repeated query values and hash", () => {
  const params = new URLSearchParams(
    "q=alpha+%26+beta&tag=a&settings=privacy&setting=privacy.confirmExternalLinks&tag=b&settings=display&setting=display.language",
  );
  assert.equal(
    settingsHref("/explore", params, null, "#results"),
    "/explore?q=alpha+%26+beta&tag=a&tag=b#results",
  );
  assert.equal(params.getAll("settings").length, 2, "input is not mutated");
});

test("selection replaces, never accumulates settings and drops stale focus target", () => {
  const params = new URLSearchParams(
    "settings=privacy&setting=privacy.confirmExternalLinks&q=hello",
  );
  assert.equal(
    settingsHref("/", params, "notifications"),
    "/?q=hello&settings=notifications",
  );
  assert.equal(
    settingsHref("/", new URLSearchParams("settings=notifications"), null),
    "/",
  );
});

test("unsafe routing destinations cannot enter the router", () => {
  for (const path of [
    "javascript:alert(1)",
    "https://example.com",
    "//example.com",
    "/\\example.com",
    "/?q=hello",
    "/#fragment",
  ]) {
    assert.throws(() =>
      settingsHref(path, new URLSearchParams(), "notifications"),
    );
  }
});

test("search is case/accent/whitespace insensitive and supports multiple terms", () => {
  for (const term of ["𝐄𝐌𝐀𝐈𝐋", "𝙀𝙈𝘼𝙄𝙇", "ＥＭＡＩＬ", "émail"]) {
    assert.deepEqual(findSettings(term), findSettings("email"), term);
  }
  assert.deepEqual(
    findSettings("  GróUP  CHATS ").map((x) => x.id),
    ["chat.allowGroupNotifications"],
  );
  assert.deepEqual(
    findSettings("email").map((x) => x.id),
    ["account.hidePersonalInfo"],
  );
  assert.deepEqual(
    findSettings("leaving warning").map((x) => x.id),
    ["privacy.confirmExternalLinks"],
  );
  assert.deepEqual(findSettings(""), []);
  assert.deepEqual(findSettings("no-such-setting"), []);
});

test("display definitions expose no fabricated user preference values", () => {
  assert.equal(
    new Set(SETTINGS_DEFINITIONS.map((x) => x.id)).size,
    SETTINGS_DEFINITIONS.length,
  );
  assert.equal(
    SETTINGS_DEFINITIONS.filter((x) => x.section === "notifications").length,
    13,
  );
  for (const setting of SETTINGS_DEFINITIONS) {
    assert.equal(
      "value" in setting || "checked" in setting || "default" in setting,
      false,
    );
    assert.notEqual(setting.section, "admin");
  }
});

test("general settings and section labels equal the bound captured English strings", () => {
  const contract = JSON.parse(
    readFileSync(
      new URL("../contracts/settings-notifications.json", import.meta.url),
      "utf8",
    ),
  );
  const strings = contract.translationCatalogue.strings;
  for (const section of SETTINGS_SECTIONS) {
    assert.equal(section.label, strings[`web.settings.tabs.${section.id}`]);
  }
  for (const [id, labelKey, descriptionKey] of [
    [
      "account.hidePersonalInfo",
      "web.auth.hide_personal_info",
      "web.settings.account.hide_personal_info_description",
    ],
    [
      "display.language",
      "settings.language_menu_title",
      "web.settings.language.description",
    ],
    [
      "privacy.confirmExternalLinks",
      "web.settings.privacy.confirm_external_links",
      "web.settings.privacy.confirm_external_links_description",
    ],
  ]) {
    const definition = SETTINGS_DEFINITIONS.find(
      (setting) => setting.id === id,
    );
    assert.equal(definition?.label, strings[labelKey]);
    assert.equal(definition?.description, strings[descriptionKey]);
  }
});

test('settings links reject URL parser control-character normalization', () => {
  for (const path of ['/\t/evil.example', '/\n/evil.example', '/\r/evil.example', '/docs\u0000/fees', '/docs\u007f']) {
    assert.throws(() => settingsHref(path,new URLSearchParams(),'privacy'), /same-origin pathname/);
  }
  assert.equal(new URL(settingsHref('/docs/fees',new URLSearchParams(),'privacy'),'https://local.invalid').origin,'https://local.invalid');
});
