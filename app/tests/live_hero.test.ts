import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import {
  parseLiveHeroCapture,
  verifyLiveHeroEvidence,
} from "../packages/frontend/src/app/live/live-hero-data.ts";
import {
  parseLiveCapture,
  sha256,
} from "../packages/frontend/src/app/live/live-data.ts";

const capture = new URL(
  "../evidence/web/objects/c45d40b52df03727",
  import.meta.url,
);
const manifest = new URL("../evidence/web/manifest.json", import.meta.url);

async function fixture() {
  const bytes = await readFile(capture);
  const source = bytes.toString("utf8");
  const match = source.match(
    /<script>self\.__next_f\.push\(([\s\S]*?)\)<\/script>/u,
  )!;
  const push = JSON.parse(match[1]);
  const rows: string[] = push[1].split("\n");
  const index = rows.findIndex((row) => row.includes('"initialHeroData":'));
  const prefix = rows[index].slice(0, rows[index].indexOf(":") + 1);
  const row = JSON.parse(rows[index].slice(prefix.length));
  const props = row[1][3];
  return {
    bytes,
    hero: props.initialHeroData,
    rewrite(change: (props: Record<string, any>, row: any) => void) {
      change(props, row);
      rows[index] = prefix + JSON.stringify(row);
      push[1] = rows.join("\n");
      return Buffer.from(
        source.replace(
          match[0],
          () => `<script>self.__next_f.push(${JSON.stringify(push)})</script>`,
        ),
      );
    },
  };
}

test("reads the six actual hero DTOs in captured order with local mint identity", async () => {
  const { bytes, hero } = await fixture();
  const streams = parseLiveHeroCapture(bytes);
  assert.equal(streams.length, 6);
  assert.deepEqual(
    streams.map((stream) => stream.mint),
    hero.map((row: { mint: string }) => row.mint),
  );
  assert.deepEqual(
    streams.map((stream) => stream.symbol),
    ["RAT", "HEATSTREET", "CIRCLES", "PJAM", "STUCK", "Shibana"],
  );
  assert.deepEqual(
    streams.map((stream) => stream.viewerCountAtCapture),
    [3, 2, 1, 3, 2, 0],
  );
  assert.equal(streams[0].title, "$RAT - Exfil Rat");
  assert.ok(
    hero.every(
      (record: object) =>
        !Object.hasOwn(record, "id") && !Object.hasOwn(record, "linkUrl"),
    ),
  );
  assert.ok(streams.every((stream) => stream.id === stream.mint));
});

test("keeps all six identities inside the separate 42-record archive without flattening them", async () => {
  const { bytes } = await fixture();
  const most = parseLiveCapture(bytes);
  const byMint = new Map(most.map((record) => [record.mint, record]));
  for (const hero of parseLiveHeroCapture(bytes))
    assert.deepEqual(hero, byMint.get(hero.mint));
  assert.equal(most.length, 42);
  assert.equal(
    new Set(
      [...most, ...parseLiveHeroCapture(bytes)].map((record) => record.mint),
    ).size,
    42,
  );
});

test("never exposes URLs, nested coin data, financial fields or playback state", async () => {
  const { bytes } = await fixture();
  for (const stream of parseLiveHeroCapture(bytes)) {
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

test("authenticates full capture bytes and manifest rather than trusting supplied historical metadata", async () => {
  const { bytes } = await fixture();
  const value = JSON.parse(await readFile(manifest, "utf8"));
  assert.equal(verifyLiveHeroEvidence(bytes, value).streams.length, 6);
  const changed = Buffer.from(bytes);
  changed[100] ^= 1;
  assert.throws(() => parseLiveHeroCapture(changed), /SHA-256 mismatch/);
  const record = value.records.find(
    (record: { url: string }) => record.url === "https://pump.fun/live",
  );
  record.final_url = "https://example.invalid/live";
  assert.throws(
    () => verifyLiveHeroEvidence(bytes, value),
    /provenance does not match/,
  );
});

test("fails the complete hero inventory for count, shape, identity, state or consistency failures", async () => {
  const changes: Array<[(props: Record<string, any>) => void, RegExp]> = [
    [
      (props) => {
        props.initialHeroData.pop();
      },
      /record count/,
    ],
    [
      (props) => {
        props.initialHeroData.push(props.initialHeroData[0]);
      },
      /record count/,
    ],
    [
      (props) => {
        props.initialHeroData[5] = props.initialHeroData[0];
      },
      /duplicate identities/,
    ],
    [
      (props) => {
        props.initialHeroData[5].id = props.initialHeroData[5].mint;
      },
      /shape is invalid/,
    ],
    [
      (props) => {
        props.initialHeroData[5].linkUrl = "/coin/excluded";
      },
      /shape is invalid/,
    ],
    [
      (props) => {
        delete props.initialHeroData[5].title;
      },
      /title is invalid/,
    ],
    [
      (props) => {
        props.initialHeroData[5].title = "different archived title";
      },
      /differs from its known/,
    ],
    [
      (props) => {
        props.initialHeroData[5].isLive = false;
      },
      /live-at-capture/,
    ],
    [
      (props) => {
        props.initialHeroData[5].symbol = "$@3";
      },
      /unresolved Flight/,
    ],
    [
      (props) => {
        props.initialHeroData[5].coin.mint = "wrong";
      },
      /coin identity/,
    ],
    [
      (props) => {
        props.initialHeroData[5].coin.extra = { initialHeroData: [] };
      },
      /hero Flight data is ambiguous/,
    ],
  ];
  for (const [change, error] of changes) {
    const control = await fixture();
    const bytes = control.rewrite(change);
    assert.throws(() => parseLiveHeroCapture(bytes, sha256(bytes)), error);
    assert.equal(parseLiveCapture(bytes, sha256(bytes)).length, 42);
  }
});

test("rejects missing or wrong-consumer HeroData without replacing it with section data", async () => {
  for (const change of [
    (props: Record<string, any>) => {
      delete props.initialHeroData;
    },
    (_props: Record<string, any>, row: any) => {
      row[1][1] = "$L999";
    },
  ]) {
    const control = await fixture();
    const bytes = control.rewrite(change);
    assert.throws(
      () => parseLiveHeroCapture(bytes, sha256(bytes)),
      /hero Flight row/,
    );
  }
});

test("binds actual initial/loop/direct-selection consumers and captured six-slot SSR state", async () => {
  const { recoverLiveHero } = await import("../scripts/original-live-hero.mjs");
  const expected = JSON.parse(
    await readFile(
      new URL("../reconstruction/live-hero/contract.json", import.meta.url),
      "utf8",
    ),
  );
  assert.deepEqual(await recoverLiveHero(), expected);
});
