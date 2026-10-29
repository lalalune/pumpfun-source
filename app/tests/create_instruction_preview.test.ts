import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { previewCreateInstruction } from "../packages/frontend/src/app/create-instruction-preview.ts";
const require = createRequire(
  new URL("../packages/sdk/package.json", import.meta.url),
);
const { PublicKey } = require("@solana/web3.js");
const { PUMP_SDK, pumpIdl } = require("./dist/index.js");
const sample = {
  name: "Offline example",
  ticker: "EXAMPLE",
  mint: "So11111111111111111111111111111111111111112",
  creator: "11111111111111111111111111111111",
  payer: "Vote111111111111111111111111111111111111111",
  metadataUri: "https://example.invalid/metadata.json",
};

test("consumer preserves exact SDK instruction bytes and IDL account order without network", async () => {
  const fetch = globalThis.fetch;
  globalThis.fetch = () => {
    throw new Error("network forbidden");
  };
  try {
    const actual = await previewCreateInstruction(sample);
    const expected = await PUMP_SDK.createV2Instruction({
      name: sample.name,
      symbol: sample.ticker,
      uri: sample.metadataUri,
      mint: new PublicKey(sample.mint),
      creator: new PublicKey(sample.creator),
      user: new PublicKey(sample.payer),
      mayhemMode: false,
      cashback: false,
      holderReward: false,
    });
    assert.equal(actual.dataHex, expected.data.toString("hex"));
    assert.equal(actual.programId, expected.programId.toBase58());
    assert.deepEqual(
      actual.accounts,
      expected.keys.map((k: any) => ({
        address: k.pubkey.toBase58(),
        isSigner: k.isSigner,
        isWritable: k.isWritable,
      })),
    );
    const idl = pumpIdl.instructions.find((i: any) => i.name === "create_v2");
    assert.equal(actual.accounts.length, idl.accounts.length);
    assert.equal(
      actual.dataHex.slice(0, 16),
      Buffer.from(idl.discriminator).toString("hex"),
    );
    assert.deepEqual(
      actual.accounts.map((a) => a.isSigner),
      idl.accounts.map((a: any) => a.signer === true),
    );
    assert.equal(actual.accounts[0].address, sample.mint);
    assert.equal(actual.accounts[5].address, sample.payer);
    const bytes = Buffer.from(actual.dataHex, "hex");
    let offset = 8;
    for (const value of [sample.name, sample.ticker, sample.metadataUri]) {
      const length = bytes.readUInt32LE(offset);
      offset += 4;
      assert.equal(
        bytes.subarray(offset, offset + length).toString("utf8"),
        value,
      );
      offset += length;
    }
    assert.deepEqual(
      bytes.subarray(offset, offset + 32),
      new PublicKey(sample.creator).toBuffer(),
    );
    offset += 32;
    assert.deepEqual(
      [...bytes.subarray(offset)],
      [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    );
    assert.deepEqual(await previewCreateInstruction(sample), actual);
  } finally {
    globalThis.fetch = fetch;
  }
});

test("input validation refuses missing keys, secret-shaped values, credentials and unsafe URI protocols", async () => {
  for (const field of ["mint", "creator", "payer"] as const) {
    for (const bad of ["", "not a key", "[1,2,3]", "word ".repeat(12)]) {
      await assert.rejects(
        previewCreateInstruction({ ...sample, [field]: bad }),
        new RegExp(field),
      );
    }
  }
  for (const bad of [
    "",
    "http://example.invalid/a",
    "javascript:alert(1)",
    "data:application/json,{}",
    "https://u:p@example.invalid/a",
    "https://example.invalid/a b",
    "ipfs:",
    "https://example.invalid/" + "x".repeat(2048),
  ]) {
    await assert.rejects(
      previewCreateInstruction({ ...sample, metadataUri: bad }),
      /Metadata URI/,
    );
  }
  await assert.rejects(
    previewCreateInstruction({ ...sample, name: " " }),
    /name/,
  );
  await assert.rejects(
    previewCreateInstruction({ ...sample, ticker: "x".repeat(11) }),
    /ticker/,
  );
});

test("explicit IPFS URI and unicode draft text are encoded, not fetched or rewritten", async () => {
  const input = {
    ...sample,
    name: "猫",
    ticker: "猫",
    metadataUri: "  ipfs://example-cid/metadata.json  ",
  };
  const result = await previewCreateInstruction(input);
  assert.ok(Buffer.from(result.dataHex, "hex").includes(Buffer.from("猫")));
  assert.ok(
    Buffer.from(result.dataHex, "hex").includes(
      Buffer.from(input.metadataUri.trim()),
    ),
  );
});

test("unpaired UTF-16 is rejected rather than silently replaced in instruction bytes", async () => {
  for (const field of ["name", "ticker", "metadataUri"] as const) {
    for (const invalid of ["\ud800", "\udc00", "a\ud800b"]) {
      await assert.rejects(
        previewCreateInstruction({ ...sample, [field]: invalid }),
        /unpaired UTF-16/,
      );
    }
  }
  const valid = await previewCreateInstruction({
    ...sample,
    name: "🐈�",
    ticker: "🐈",
  });
  assert.ok(Buffer.from(valid.dataHex, "hex").includes(Buffer.from("🐈�")));
});

test("valid leading BOM text is preserved, not mistaken for malformed UTF-16", async () => {
  const result = await previewCreateInstruction({
    ...sample,
    name: "\ufeffName",
    ticker: "\ufeffN",
  });
  const bytes = Buffer.from(result.dataHex, "hex");
  assert.ok(bytes.includes(Buffer.from("\ufeffName")));
  assert.ok(bytes.includes(Buffer.from("\ufeffN")));
});
