import assert from "node:assert/strict";
import { test } from "node:test";
import {
  validateDraft,
  validateDraftField,
  CREATE_LIMITS,
} from "../packages/frontend/src/app/create-coin-validation.ts";

test("name validation rejects multibyte text above32UTF8bytes despite fitting native32codeunits", () => {
  const value = "漢".repeat(11);
  assert.equal(value.length, 11);
  assert.equal(new Blob([value]).size, 33);
  assert.match(validateDraftField("name", value) ?? "", /32.*UTF-8 bytes/);
});
test("ticker validation rejects12byte emoji text which fits native10codeunits", () => {
  const value = "💚".repeat(3);
  assert.equal(value.length, 6);
  assert.equal(new Blob([value]).size, 12);
  assert.match(validateDraftField("ticker", value) ?? "", /10.*UTF-8 bytes/);
});
test("byte limits are inclusive and preserve valid Unicode without normalization or alphabet rules", () => {
  for (const [field, value] of [
    ["name", "漢".repeat(10) + "ab"],
    ["name", "💚".repeat(8)],
    ["name", "a".repeat(32)],
    ["ticker", "漢漢漢a"],
    ["ticker", "💚💚ab"],
    ["ticker", "$? 混合"],
  ]) {
    assert.equal(new Blob([value]).size <= CREATE_LIMITS[field], true);
    assert.equal(validateDraftField(field, value), undefined);
  }
});
test("UTF8counts include combining/BOM/surrogate replacement bytes exactly as nativeBlob", () => {
  for (const value of [
    "e\u0301".repeat(11),
    "a" + "\ufeff".repeat(11),
    "\ud800".repeat(11),
    "\udc00".repeat(11),
  ]) {
    assert.equal(value.length <= 32, true);
    assert.ok(new Blob([value]).size > 32);
    assert.match(validateDraftField("name", value) ?? "", /UTF-8 bytes/);
  }
  for (const value of [
    "e\u0301".repeat(10) + "ab",
    "\ufeff".repeat(10) + "ab",
    "\ud800".repeat(10) + "ab",
  ]) {
    assert.equal(new Blob([value]).size, 32);
    assert.equal(validateDraftField("name", value), undefined);
  }
});
test("description remains a2000codeunit limit, and existing required/URL validation stays intact", () => {
  const description = "💚".repeat(1000);
  assert.equal(description.length, 2000);
  assert.equal(new Blob([description]).size, 4000);
  assert.equal(validateDraftField("description", description), undefined);
  assert.match(
    validateDraftField("description", description + "x") ?? "",
    /2,000/,
  );
  assert.match(validateDraftField("name", " \t") ?? "", /Enter a coin name/);
  assert.match(validateDraftField("ticker", "") ?? "", /Enter a ticker/);
  assert.match(
    validateDraftField("website", "javascript:alert(1)") ?? "",
    /HTTPS/,
  );
});
test("complete local draft reports byte-invalid fields and preserves valid descriptive values", () => {
  const image = new File([new Uint8Array([1])], "coin.png", {
    type: "image/png",
  });
  const draft = {
    name: "漢".repeat(11),
    ticker: "💚💚💚",
    description: "",
    website: "",
    twitter: "",
    telegram: "",
  };
  const errors = validateDraft(draft, image);
  assert.match(errors.name ?? "", /32.*UTF-8/);
  assert.match(errors.ticker ?? "", /10.*UTF-8/);
  const valid = { ...draft, name: "漢".repeat(10) + "ab", ticker: "💚💚ab" };
  assert.deepEqual(validateDraft(valid, image), {});
  assert.equal(valid.name, "漢".repeat(10) + "ab");
});
