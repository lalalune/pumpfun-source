import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import {
  LIVE_HIGHEST_MARKET_CAP_COUNT,
  parseHighestMarketCapCapture,
  parseLiveCapture,
  sha256,
  verifyLiveEvidence,
} from "../packages/frontend/src/app/live/live-data.ts";

const capture = new URL(
  "../evidence/web/objects/c45d40b52df03727",
  import.meta.url,
);
const manifest = new URL("../evidence/web/manifest.json", import.meta.url);

async function fixture() {
  const bytes = await readFile(capture);
  const source = bytes.toString("utf8");
  const matches = [
    ...source.matchAll(
      /<script>self\.__next_f\.push\(([\s\S]*?)\)<\/script>/gu,
    ),
  ];
  assert.equal(matches.length, 1);
  const push = JSON.parse(matches[0][1]);
  const rows: string[] = push[1].split("\n");
  const index = rows.findIndex((row) => row.includes('"initialSectionData":'));
  assert.ok(index >= 0);
  const prefix = rows[index].slice(0, rows[index].indexOf(":") + 1);
  const row = JSON.parse(rows[index].slice(prefix.length));
  const sections = row[1][3].initialSectionData;
  return {
    bytes,
    sections,
    rewrite(change: (value: Record<string, unknown>[][]) => void) {
      change(sections);
      rows[index] = prefix + JSON.stringify(row);
      push[1] = rows.join("\n");
      return Buffer.from(
        source.replace(
          matches[0][0],
          () => `<script>self.__next_f.push(${JSON.stringify(push)})</script>`,
        ),
      );
    },
  };
}

test("authenticates all 24 separately captured cards in exact second-section order", async () => {
  const { bytes, sections } = await fixture();
  const streams = parseHighestMarketCapCapture(bytes);
  assert.equal(streams.length, LIVE_HIGHEST_MARKET_CAP_COUNT);
  assert.equal(new Set(streams.map((stream) => stream.id)).size, 24);
  assert.deepEqual(
    streams.map((stream) => stream.id),
    sections[1].map((row: { id: string }) => row.id),
  );
  assert.deepEqual(
    streams.slice(0, 5).map((stream) => stream.symbol),
    ["RAT", "HEATSTREET", "CIRCLES", "PJAM", "STUCK"],
  );
  assert.deepEqual(
    streams.slice(0, 5).map((stream) => stream.viewerCountAtCapture),
    [3, 2, 1, 3, 2],
  );
  assert.equal(
    sha256(Buffer.from(JSON.stringify(streams.map((stream) => stream.id)))),
    "41be8fb2bc2c145405dbbf8ae3c0a2f095f0e35441cd21d0a6c7076df0dddd8d",
  );
  assert.equal(streams[0].title, "$RAT - Exfil Rat");
});

test("keeps section membership distinct without manufacturing additional unique streams", async () => {
  const { bytes } = await fixture();
  const most = parseLiveCapture(bytes);
  const highest = parseHighestMarketCapCapture(bytes);
  assert.equal(most.length, 42);
  assert.notDeepEqual(most.slice(0, 24), highest);
  const firstById = new Map(most.map((stream) => [stream.id, stream]));
  for (const stream of highest)
    assert.deepEqual(stream, firstById.get(stream.id));
  assert.equal(
    new Set([...most, ...highest].map((stream) => stream.id)).size,
    42,
  );
});

test("projects only validated historical metadata, discarding media and nested coin fields", async () => {
  const { bytes } = await fixture();
  for (const stream of parseHighestMarketCapCapture(bytes)) {
    assert.deepEqual(Object.keys(stream).sort(), [
      "creatorAddress",
      "id",
      "mint",
      "symbol",
      "title",
      "viewerCountAtCapture",
      "wasLiveAtCapture",
    ]);
    assert.equal(stream.wasLiveAtCapture, true);
    assert.equal(JSON.stringify(stream).includes("https://"), false);
  }
});

test("rejects changed bytes and all changed provenance before exposing the second section", async () => {
  const { bytes } = await fixture();
  const manifestValue = JSON.parse(await readFile(manifest, "utf8"));
  assert.equal(
    verifyLiveEvidence(bytes, manifestValue, "highest-market-cap").streams
      .length,
    24,
  );
  const changed = Buffer.from(bytes);
  changed[500] ^= 1;
  assert.throws(
    () => parseHighestMarketCapCapture(changed),
    /SHA-256 mismatch/,
  );
  for (const field of [
    "url",
    "final_url",
    "status",
    "path",
    "bytes",
    "sha256",
  ]) {
    const value = structuredClone(manifestValue);
    const record = value.records.find(
      (record: { url?: string }) => record.url === "https://pump.fun/live",
    );
    record[field] = field === "status" ? 201 : "changed";
    assert.throws(
      () => verifyLiveEvidence(bytes, value, "highest-market-cap"),
      /Live record is not unique|provenance does not match/,
    );
  }
  assert.throws(
    () =>
      verifyLiveEvidence(
        bytes,
        { ...manifestValue, captured_at: "changed" },
        "highest-market-cap",
      ),
    /timestamp does not match/,
  );
});

test("fails the complete selected section for missing, extra, duplicate, malformed or unresolved records", async () => {
  const mutations: Array<
    [(sections: Record<string, unknown>[][]) => void, RegExp]
  > = [
    [
      (sections) => {
        sections[1].pop();
      },
      /record count/,
    ],
    [
      (sections) => {
        sections[1].push(sections[1][0]);
      },
      /record count/,
    ],
    [
      (sections) => {
        sections[1][23] = sections[1][0];
      },
      /duplicate identities/,
    ],
    [
      (sections) => {
        delete sections[1][23].title;
      },
      /title is invalid/,
    ],
    [
      (sections) => {
        sections[1][23].isLive = false;
      },
      /live-at-capture/,
    ],
    [
      (sections) => {
        sections[1][23].viewerCount = -1;
      },
      /viewer count/,
    ],
    [
      (sections) => {
        sections[1][23].symbol = "$@3";
      },
      /unresolved Flight/,
    ],
    [
      (sections) => {
        sections[1][23].coin = { mint: "wrong" };
      },
      /coin identity/,
    ],
    [
      (sections) => {
        sections[1][23].playlistToken = "not-exposed";
      },
      /unexpected fields/,
    ],
  ];
  for (const [mutate, message] of mutations) {
    const control = await fixture();
    const changed = control.rewrite(mutate);
    assert.throws(
      () => parseHighestMarketCapCapture(changed, sha256(changed)),
      message,
    );
    assert.equal(parseLiveCapture(changed, sha256(changed)).length, 42);
  }
});

test("rejects absent or non-array second sections without substituting the first", async () => {
  for (const mutate of [
    (sections: Record<string, unknown>[][]) => {
      sections.pop();
    },
    (sections: Record<string, unknown>[][]) => {
      (sections as unknown[])[1] = null;
    },
  ]) {
    const control = await fixture();
    const changed = control.rewrite(mutate);
    assert.throws(
      () => parseHighestMarketCapCapture(changed, sha256(changed)),
      /section is missing|not an array/,
    );
  }
});

test("binds the actual original registry, Flight consumer, section label and Show-all route", async () => {
  const { recoverHighestMarketCapSection } = await import(
    "../scripts/original-live-highest.mjs"
  );
  const actual = await recoverHighestMarketCapSection();
  const expected = JSON.parse(
    await readFile(
      new URL("../reconstruction/live-highest/contract.json", import.meta.url),
      "utf8",
    ),
  );
  assert.deepEqual(actual, expected);
});
