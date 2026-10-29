/** SDK-only account contract. No captured JavaScript execution or SDK edits. */
import assert from "node:assert/strict";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { parse } from "@babel/parser";
import {
  decodeSource,
  exactlyOne,
  findNodes,
  sha256,
} from "../original-contracts/source.mjs";
const root = new URL("../../", import.meta.url);
const archive = new URL("evidence/sdk/pump-sdk-4.3.1.tgz", root);
assert.equal(
  sha256(await readFile(archive)),
  "c8ff4e850651c81e9f488bfc6dffb4513a041bb4bca0819879dc19d9a72a4641",
);
const paths = [
  "src/idl/pump_amm.json",
  "src/swap/pda.ts",
  "src/swap/offlinePumpAmm.ts",
  "src/swap/onlinePumpAmm.ts",
  "src/swap/index.ts",
  "src/onlineSdk.ts",
  "src/swap/types.ts",
];
const sources = new Map();
for (const path of paths) {
  const bytes = await readFile(new URL(`packages/sdk/${path}`, root));
  assert.deepEqual(
    bytes,
    execFileSync("tar", ["-xOf", fileURLToPath(archive), `package/${path}`]),
  );
  const decoded = decodeSource(bytes);
  sources.set(path, {
    ...decoded,
    bytes,
    ast: path.endsWith(".ts")
      ? parse(decoded.text, { sourceType: "module", plugins: ["typescript"] })
      : null,
  });
}
const idl = JSON.parse(sources.get(paths[0]).text);
const account = exactlyOne(
  idl.accounts.filter((x) => x.name === "UserVolumeAccumulator"),
  "account",
);
const layout = exactlyOne(
  idl.types.filter((x) => x.name === account.name),
  "layout",
).type;
assert.equal(layout.kind, "struct");
const widths = { pubkey: 32, bool: 1, u64: 8, i64: 8 };
let end = 8;
const fields = layout.fields.map((field) => {
  const width = widths[field.type];
  assert.ok(width, `unsupported field ${field.name}`);
  const start = end;
  end += width;
  return {
    name: field.name,
    decoded: field.name.replace(/_([a-z])/g, (_, c) => c.toUpperCase()),
    type: field.type,
    bytes: [start, end],
  };
});
assert.equal(end, 90);
assert.ok(
  !fields.some((x) => x.name.includes("stable")),
  "Absent stable counters must not become zero-valued fields",
);
const fn = (name) => (n) =>
  n.type === "FunctionDeclaration" && n.id?.name === name;
const method = (name) => (n) =>
  n.type === "ClassMethod" && n.key?.name === name;
const pda = exactlyOne(
  findNodes(sources.get("src/swap/pda.ts").ast, fn("userVolumeAccumulatorPda")),
  "AMM PDA",
);
const seed = exactlyOne(
  findNodes(pda, (n) => n.type === "StringLiteral"),
  "PDA seed",
).value;
assert.equal(seed, "user_volume_accumulator");
const program = exactlyOne(
  findNodes(
    sources.get("src/swap/pda.ts").ast,
    (n) =>
      n.type === "VariableDeclarator" && n.id?.name === "PUMP_AMM_PROGRAM_ID",
  ),
  "AMM program",
);
assert.equal(program.init.arguments[0].value, idl.address);
function witness(path, predicate, label) {
  const source = sources.get(path);
  const node = exactlyOne(findNodes(source.ast, predicate), label);
  const bytes = source.bytes.subarray(
    source.byteOffsets[node.start],
    source.byteOffsets[node.end],
  );
  assert.ok(
    source.byteOffsets[node.start] >= 0 && source.byteOffsets[node.end] >= 0,
  );
  return {
    label,
    path: `packages/sdk/${path}`,
    sourceSha256: sha256(source.bytes),
    utf16: [node.start, node.end],
    utf8: [source.byteOffsets[node.start], source.byteOffsets[node.end]],
    sha256: sha256(bytes),
  };
}
const contract = {
  sdkVersion: "4.3.1",
  programId: idl.address,
  pdaSeed: seed,
  account: account.name,
  discriminator: account.discriminator,
  minimumBytes: end,
  fields,
};
const proof = {
  manifestBoundary: {
    note: "The repository SDK package manifest is already adapted for this workspace; it is not one of the archive-identical source inputs. Neither manifest is changed here.",
    published: JSON.parse(
      execFileSync("tar", [
        "-xOf",
        fileURLToPath(archive),
        "package/package.json",
      ]).toString(),
    ).exports,
    workspace: JSON.parse(
      await readFile(new URL("packages/sdk/package.json", root), "utf8"),
    ).exports,
    workspaceSha256: sha256(
      await readFile(new URL("packages/sdk/package.json", root)),
    ),
    publishedSha256: sha256(
      execFileSync("tar", [
        "-xOf",
        fileURLToPath(archive),
        "package/package.json",
      ]),
    ),
  },
  authority:
    "Published SDK/IDL account reads only; independent public PumpSwap record view, no original frontend/private API/entitlement parity",
  archiveSha256: sha256(await readFile(archive)),
  sources: paths.map((path) => ({
    path: `packages/sdk/${path}`,
    sha256: sha256(sources.get(path).bytes),
  })),
  witnesses: [
    witness(
      "src/swap/pda.ts",
      fn("userVolumeAccumulatorPda"),
      "AMM-specific wallet PDA namespace",
    ),
    witness(
      "src/swap/pda.ts",
      (n) =>
        n.type === "VariableDeclarator" && n.id?.name === "PUMP_AMM_PROGRAM_ID",
      "Fixed AMM program constant matches IDL",
    ),
    witness(
      "src/swap/offlinePumpAmm.ts",
      method("decodeUserVolumeAccumulator"),
      "Actual strict AMM decoder, no nullable failure swallowing",
    ),
    witness(
      "src/swap/onlinePumpAmm.ts",
      method("fetchUserVolumeAccumulator"),
      "Actual nullable AMM wallet account read",
    ),
    witness(
      "src/onlineSdk.ts",
      method("fetchUserVolumeAccumulatorTotalStats"),
      "Used consumer reads both program records; this view does not aggregate or substitute missing zeros",
    ),
    witness(
      "src/swap/onlinePumpAmm.ts",
      method("getTotalUnclaimedTokens"),
      "AMM incentive calculation also reads its Global record; not run by this view",
    ),
    witness(
      "src/swap/types.ts",
      (n) =>
        n.type === "TSInterfaceDeclaration" &&
        n.id?.name === "UserVolumeAccumulator",
      "Published handwritten type omits three actual IDL fields; local unknown validation is required",
    ),
  ],
  distinctions: [
    "AMM known prefix90 bytes, Pump106 bytes",
    "No stable-cashback fields in AMM layout",
    "Same seed/discriminator name does not remove separate program/PDA ownership",
    "Stored counters and flags do not establish current entitlement or verified payout history",
  ],
};
for (const [path, value] of [
  ["packages/frontend/src/app/amm-wallet-record/contract.json", contract],
  ["research/amm-wallet-record-20261029/SOURCE.json", proof],
]) {
  const target = new URL(path, root),
    bytes = JSON.stringify(value, null, 2) + "\n";
  if (process.argv.includes("--check"))
    assert.equal(await readFile(target, "utf8"), bytes, path);
  else {
    await mkdir(new URL(".", target), { recursive: true });
    await writeFile(target, bytes);
  }
}
console.log(
  "PumpSwap published account contract verified:7 archive-identical sources,90-byte known layout,7 static witnesses; SDK unchanged",
);
