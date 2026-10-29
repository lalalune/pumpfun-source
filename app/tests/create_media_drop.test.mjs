import test from "node:test";
import assert from "node:assert/strict";
import {
  hasDraggedFile,
  readDroppedFile,
} from "../packages/frontend/src/app/create-media-drop.ts";

const file = () =>
  new File(["synthetic image"], "image.png", { type: "image/png" });
const item = (value, overrides = {}) => ({
  kind: "file",
  getAsFile: () => value,
  ...overrides,
});
const drop = (items = [], files = []) => ({ items, files });

test("one local file is returned without reading or altering its bytes", () => {
  const value = file();
  value.arrayBuffer = value.text = () => {
    throw new Error("must not read file contents");
  };
  assert.equal(readDroppedFile(drop([item(value)], [value])).file, value);
});

test("FileList-only browser port accepts exactly one file", () => {
  const value = file();
  assert.equal(readDroppedFile(drop([], [value])).file, value);
});

test("multiple file items are rejected before materializing any file", () => {
  const unread = item(null, {
    getAsFile() {
      assert.fail("multiple files must not be read");
    },
  });
  assert.match(readDroppedFile(drop([unread, unread])).error, /exactly one/);
});

test("multiple FileList entries are rejected even if items are missing or partial", () => {
  const value = file();
  for (const items of [[], [item(value)]])
    assert.match(
      readDroppedFile(drop(items, [value, value])).error,
      /exactly one/,
    );
});

test("folders are rejected without reading their file or walking their entries", () => {
  const directory = item(null, {
    webkitGetAsEntry: () => ({
      isDirectory: true,
      createReader() {
        assert.fail("no traversal");
      },
    }),
    getAsFile() {
      assert.fail("directory must not be materialized");
    },
  });
  assert.match(readDroppedFile(drop([directory])).error, /not a folder/);
});

test("ordinary file entries remain accepted", () => {
  const value = file();
  assert.equal(
    readDroppedFile(
      drop([item(value, { webkitGetAsEntry: () => ({ isDirectory: false }) })]),
    ).file,
    value,
  );
});

test("unavailable entry metadata does not prevent a readable file", () => {
  const value = file();
  assert.equal(
    readDroppedFile(drop([item(value, { webkitGetAsEntry: () => null })])).file,
    value,
  );
});

test("unreadable file items fail rather than falling back to a different FileList entry", () => {
  assert.match(
    readDroppedFile(drop([item(null)], [file()])).error,
    /could not be read/,
  );
});

test("entry and file access errors produce local feedback without escaping", () => {
  for (const method of ["webkitGetAsEntry", "getAsFile"]) {
    assert.match(
      readDroppedFile(
        drop([
          item(file(), {
            [method]() {
              throw new Error("unavailable");
            },
          }),
        ]),
      ).error,
      /could not be read/,
    );
  }
});

test("text, HTML, URLs and empty drops are never read or followed", () => {
  for (const type of ["text/plain", "text/html", "text/uri-list"]) {
    assert.match(
      readDroppedFile(
        drop([
          {
            kind: "string",
            type,
            getAsString() {
              assert.fail("do not read dropped strings");
            },
          },
        ]),
      ).error,
      /not text or a link/,
    );
  }
  assert.match(readDroppedFile(drop()).error, /local image or video/);
});

test("string metadata accompanying a local file is ignored", () => {
  const value = file();
  assert.equal(
    readDroppedFile(
      drop([
        {
          kind: "string",
          getAsString() {
            assert.fail("no string read");
          },
        },
        item(value),
      ]),
    ).file,
    value,
  );
});

test("drag hints support protected FileList mode without promising type validation", () => {
  assert.equal(hasDraggedFile({ items: [], types: ["Files"] }), true);
  assert.equal(hasDraggedFile({ items: [{ kind: "file" }], types: [] }), true);
  assert.equal(
    hasDraggedFile({ items: [{ kind: "string" }], types: ["text/uri-list"] }),
    false,
  );
  assert.equal(hasDraggedFile({ items: [], types: [] }), false);
});
