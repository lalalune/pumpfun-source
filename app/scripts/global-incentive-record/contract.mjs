/** Published SDK attribution only; captured frontend factories are not evaluated. */
import assert from "node:assert/strict";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
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
const archiveSha256 = sha256(await readFile(archive));
assert.equal(
  archiveSha256,
  "c8ff4e850651c81e9f488bfc6dffb4513a041bb4bca0819879dc19d9a72a4641",
);
const sources = new Map();
for (const path of [
  "src/idl/pump.json",
  "src/pda.ts",
  "src/sdk.ts",
  "src/state.ts",
  "src/onlineSdk.ts",
  "src/tokenIncentives.ts",
]) {
  const bytes = await readFile(new URL(`packages/sdk/${path}`, root));
  assert.deepEqual(
    bytes,
    execFileSync("tar", ["-xOf", fileURLToPath(archive), `package/${path}`]),
  );
  const source = decodeSource(bytes);
  sources.set(path, {
    ...source,
    bytes,
    ast: path.endsWith(".ts")
      ? parse(source.text, { sourceType: "module", plugins: ["typescript"] })
      : null,
  });
}
const idl = JSON.parse(sources.get("src/idl/pump.json").text);
const account = exactlyOne(
  idl.accounts.filter((x) => x.name === "GlobalVolumeAccumulator"),
  "account",
);
const layout = exactlyOne(
  idl.types.filter((x) => x.name === account.name),
  "layout",
).type;
assert.equal(layout.kind, "struct");
let end = 8;
const fields = layout.fields.map((field) => {
  const count = typeof field.type === "object" ? field.type.array?.[1] : 1;
  const type =
    typeof field.type === "object" ? field.type.array?.[0] : field.type;
  assert.ok(
    ["i64", "u64", "pubkey"].includes(type) &&
      Number.isInteger(count) &&
      count > 0,
  );
  const start = end;
  end += (type === "pubkey" ? 32 : 8) * count;
  return {
    name: field.name,
    decoded: field.name.replace(/_([a-z])/g, (_, c) => c.toUpperCase()),
    type,
    count,
    bytes: [start, end],
  };
});
assert.equal(end, 544);
const pdaNode = exactlyOne(
  findNodes(
    sources.get("src/pda.ts").ast,
    (n) =>
      n.type === "VariableDeclarator" &&
      n.id?.name === "GLOBAL_VOLUME_ACCUMULATOR_PDA",
  ),
  "used PDA",
);
assert.equal(pdaNode.init?.callee?.name, "pumpPda");
const seed = exactlyOne(
  findNodes(pdaNode, (n) => n.type === "StringLiteral"),
  "seed",
).value;
assert.equal(seed, "global_volume_accumulator");
const requireFrontend = createRequire(
  new URL("packages/frontend/package.json", root),
);
const { PublicKey } = requireFrontend("@solana/web3.js");
const [pda] = PublicKey.findProgramAddressSync(
  [Buffer.from(seed)],
  new PublicKey(idl.address),
);
const contract = {
  sdkVersion: "4.3.1",
  programId: idl.address,
  recordPda: pda.toBase58(),
  pdaSeed: seed,
  account: account.name,
  discriminator: account.discriminator,
  minimumBytes: end,
  fields,
};
const witness = (path, node, label) => {
  const source = sources.get(path),
    byteRange = [source.byteOffsets[node.start], source.byteOffsets[node.end]];
  assert.ok(byteRange.every((x) => Number.isInteger(x) && x >= 0));
  return {
    source: `packages/sdk/${path}`,
    sourceSha256: sha256(source.bytes),
    label,
    utf16: [node.start, node.end],
    bytes: byteRange,
    sha256: sha256(source.bytes.subarray(...byteRange)),
  };
};
const method = (path, name) =>
  exactlyOne(
    findNodes(
      sources.get(path).ast,
      (n) => n.type === "ClassMethod" && n.key?.name === name,
    ),
    name,
  );
const witnesses = [
  witness("src/pda.ts", pdaNode, "fixed Pump Global volume PDA"),
  witness(
    "src/sdk.ts",
    method("src/sdk.ts", "decodeGlobalVolumeAccumulator"),
    "actual published account decoder",
  ),
  witness(
    "src/onlineSdk.ts",
    method("src/onlineSdk.ts", "getTotalUnclaimedTokens"),
    "used Global and user account dependency; computation not enabled by this inspector",
  ),
  witness(
    "src/onlineSdk.ts",
    method("src/onlineSdk.ts", "getCurrentDayTokens"),
    "separate current-day computation dependency; not enabled",
  ),
  witness(
    "src/state.ts",
    exactlyOne(
      findNodes(
        sources.get("src/state.ts").ast,
        (n) =>
          n.type === "TSInterfaceDeclaration" &&
          n.id?.name === "GlobalVolumeAccumulator",
      ),
      "SDK state",
    ),
    "published signed timestamps and exact array fields",
  ),
];
const result = {
  authority:
    "Published SDK source; independent public configuration inspector, not upstream UI/server equivalence",
  archiveSha256,
  sourceFiles: [...sources].map(([path, s]) => ({
    path: `packages/sdk/${path}`,
    sha256: sha256(s.bytes),
    archiveEqual: true,
  })),
  contract,
  witnesses,
  limits: [
    "No tokenIncentives calculation is invoked",
    "Stored schedule and aggregate raw integers do not establish eligibility, an active campaign, claimability or current value",
    "No claim, signature, account mutation or private API",
  ],
};
const outputs = [
  [
    new URL(
      "packages/frontend/src/app/global-incentive-record/contract.json",
      root,
    ),
    contract,
  ],
  [
    new URL("research/global-incentive-record-20261029/SOURCE.json", root),
    result,
  ],
];
for (const [path, value] of outputs) {
  const text = JSON.stringify(value, null, 2) + "\n";
  if (process.argv.includes("--check"))
    assert.equal(await readFile(path, "utf8"), text);
  else {
    await mkdir(new URL(".", path), { recursive: true });
    await writeFile(path, text);
  }
}
console.log(
  "Global incentive record source verified: 6 archive-equal SDK files, 5 AST witnesses, 544-byte layout",
);
