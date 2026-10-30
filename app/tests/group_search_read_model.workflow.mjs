import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { once } from "node:events";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { createHash } from "node:crypto";
import { createGroupSearchReadModel } from "../reconstruction/group-search-read-model/client.mjs";
const app = fileURLToPath(new URL("..", import.meta.url)),
  require = createRequire(
    new URL("../packages/frontend/package.json", import.meta.url),
  ),
  schemaPath = require.resolve("next/dist/compiled/zod"),
  { z } = require("next/dist/compiled/zod"),
  sha = (b) => createHash("sha256").update(b).digest("hex");
// Explicit synthetic response capabilities, not original endpoint/runtime schemas.
function fixture() {
  const str = () => z.string(),
    num = () => z.number();
  const row = z.object({
    userId: str(),
    username: str(),
    bio: str(),
    profileImageUrl: str(),
    headerImageUrl: str(),
    followerCount: num(),
    followingCount: num(),
    createdAt: str(),
    updatedAt: str(),
    walletAddress: str(),
    isVerified: z.boolean(),
    verifiedBadgeVisible: z.boolean(),
    resolvedAvatarDecoration: str(),
    memberCount: num(),
  });
  const user = z.object({
    address: str(),
    userId: str(),
    username: str(),
    profile_image: str(),
    header_image_url: str(),
    member_count: num(),
    bio: str(),
    followers: num(),
    following: num(),
    active_competition_entry: z
      .object({
        competition_id: str(),
        competition_slug: str(),
        entry_id: str(),
        phase: str(),
      })
      .nullish(),
  });
  return {
    z,
    contract: {
      "GET /groups/search": { response: z.object({ results: row.array() }) },
      "GET /users/{id}": { response: user },
    },
  };
}
const rows = [
  {
    userId: "synthetic-group",
    username: "",
    bio: "",
    profileImageUrl: "",
    headerImageUrl: null,
    followerCount: 0,
    followingCount: null,
    walletAddress: "",
    isVerified: null,
    verifiedBadgeVisible: false,
    resolvedAvatarDecoration: null,
    memberCount: 0,
    createdAt: null,
    updatedAt: null,
    kind: "GrOuP",
    extra: true,
  },
  { userId: "synthetic-person", username: null, kind: "unknown" },
];
const profile = {
  address: "synthetic-address",
  userId: "other-returned-id",
  username: "",
  profile_image: "",
  header_image_url: null,
  member_count: 0,
  bio: "",
  followers: 0,
  following: 0,
  active_competition_entry: {
    competition_id: "synthetic-competition",
    competition_slug: "synthetic-slug",
    entry_id: "",
    phase: "synthetic-phase",
  },
  extra: true,
};
test(
  "complete group readers/schema/projections in all five physical contexts with real local reads and explicit schema/client ports",
  { timeout: 30000 },
  async () => {
    const output = process.env.PUMP_GROUP_SEARCH_READ_MODEL_OUTPUT,
      receipt = {
        scope:
          "Source constructor/read/parse/projection flow with explicitly synthetic response schemas/API ports only; no original runtime/schema/backend/auth/data/UI equivalence",
        observations: [],
        requests: [],
        apiCalls: [],
        inputs: [],
        dependencies: [],
      };
    let server,
      base,
      mode = "normal",
      heldResolve,
      lastPortError;
    try {
      const contract = JSON.parse(
        await readFile(
          path.join(
            app,
            "reconstruction/group-search-read-model/contract.json",
          ),
          "utf8",
        ),
      );
      for (const name of [
        "reconstruction/group-search-read-model/client.mjs",
        "reconstruction/group-search-read-model/contract.json",
        "scripts/original-group-search-read-model.mjs",
        "tests/original_group_search_read_model.test.mjs",
        "tests/group_search_read_model.workflow.mjs",
        "pnpm-lock.yaml",
        "packages/frontend/package.json",
      ]) {
        const b = await readFile(path.join(app, name));
        receipt.inputs.push({ path: name, bytes: b.length, sha256: sha(b) });
      }
      for (const file of [schemaPath, require.resolve("next/package.json")]) {
        const b = await readFile(file);
        receipt.dependencies.push({
          path: path.relative(app, file),
          bytes: b.length,
          sha256: sha(b),
        });
      }
      receipt.nodeVersion = process.version;
      receipt.fixtureRuntime =
        "Existing lock-pinned Next compiled schema namespace; synthetic capabilities only, no original Zod parity";
      server = createServer((req, res) => {
        receipt.requests.push({ method: req.method, path: req.url, mode });
        assert.equal(req.method, "GET");
        if (mode === "hold") {
          heldResolve();
          req.once("close", () =>
            receipt.observations.push({
              name: "held native local request closed after abort",
            }),
          );
          return;
        }
        if (mode === "status") {
          res.writeHead(503).end("{}");
          return;
        }
        if (mode === "bad-json") {
          res.writeHead(200).end("{");
          return;
        }
        res.setHeader("content-type", "application/json");
        res.end(
          JSON.stringify(
            req.url.startsWith("/synthetic/profile")
              ? profile
              : { results: rows, extra: true },
          ),
        );
      });
      server.listen(0, "127.0.0.1");
      await once(server, "listening");
      base = "http://127.0.0.1:" + server.address().port;
      const api = async (op, options) => {
        assert(["GET /users/{id}", "GET /groups/search"].includes(op));
        receipt.apiCalls.push({
          op,
          params: options.params,
          query: options.query,
          queryKeys: options.query ? Object.keys(options.query) : undefined,
          hasSignal: options.signal instanceof AbortSignal,
        });
        const q = new URLSearchParams();
        for (const [k, v] of Object.entries(options.params ?? options.query))
          if (v !== undefined) q.set(k, String(v));
        try {
          const r = await fetch(
            base +
              (options.params ? "/synthetic/profile" : "/synthetic/search") +
              "?" +
              q,
            { signal: options.signal },
          );
          if (!r.ok) {
            const e = Error("Synthetic API port status");
            e.status = r.status;
            throw e;
          }
          return await r.json();
        } catch (e) {
          lastPortError = e;
          throw e;
        }
      };
      const ports = fixture();
      for (const context of contract.contexts) {
        const model = createGroupSearchReadModel({
            ...ports,
            context: context.source,
          }),
          signal = new AbortController().signal;
        let actualOptions;
        const exactApi = (op, o) => {
          actualOptions = o;
          assert.strictEqual(o.signal, signal);
          return api(op, o);
        };
        const search = await model.searchGroups({
          api: exactApi,
          searchTerm: "synthetic & query",
          offset: 40,
          signal,
        });
        assert.deepEqual(actualOptions.query, {
          searchTerm: "synthetic & query",
          limit: 20,
          offset: 40,
        });
        assert.equal(search.length, 2);
        assert.equal(search[0].kind, "group");
        assert.equal(search[1].kind, "person");
        assert.equal(search[0].bio, null);
        assert.equal(search[0].profileImage, null);
        assert.equal(search[0].walletAddress, null);
        assert.equal(search[0].verifiedBadgeVisible, false);
        assert.equal(search[1].verifiedBadgeVisible, true);
        assert.equal(search[1].username, "");
        assert.equal(search[1].memberCount, 0);
        assert(!Object.hasOwn(search[0], "extra"));
        const display = model.projectSearchRow(search[0]);
        assert.deepEqual(display, {
          groupId: "synthetic-group",
          username: null,
          bio: null,
          profileImage: null,
          headerImageUrl: null,
          memberCount: 0,
          followers: 0,
          following: 0,
          activeCompetitionEntry: null,
        });
        const group = await model.readGroup({
          api: exactApi,
          groupId: "requested / group",
          signal,
        });
        assert.deepEqual(actualOptions.params, { id: "requested / group" });
        assert.equal(group.groupId, "requested / group");
        assert.equal(group.username, "");
        assert.equal(group.profileImage, "");
        assert.equal(group.bio, "");
        assert.equal(group.followers, 0);
        assert.equal(group.memberCount, 0);
        assert.equal(group.activeCompetitionEntry.entryId, "");
        assert.equal(
          group.activeCompetitionEntry.competitionId,
          "synthetic-competition",
        );
        assert(!Object.hasOwn(group, "userId"));
        assert(!Object.hasOwn(group, "extra"));
        receipt.observations.push({
          name: "complete request/parse and actual SearchRows/RecentTerms projections",
          context: context.source,
          search,
          display,
          group,
          sourceSignalIdentity: true,
          defaultLimit: 20,
        });
        const error = Error("Synthetic opaque rejection");
        await assert.rejects(
          model.searchGroups({
            api: () => Promise.reject(error),
            searchTerm: "x",
          }),
          (e) => e === error,
        );
        await assert.rejects(
          model.readGroup({ api: () => Promise.reject(error), groupId: "x" }),
          (e) => e === error,
        );
        await assert.rejects(
          model.searchGroups({
            api: async () => ({ results: [{}] }),
            searchTerm: "x",
          }),
          (e) => Array.isArray(e.issues),
        );
        await assert.rejects(
          model.readGroup({
            api: async () => ({ username: 123 }),
            groupId: "x",
          }),
          (e) => Array.isArray(e.issues),
        );
        let captured;
        assert.deepEqual(
          await model.searchGroups({
            api: async (op, o) => {
              captured = o;
              return { results: [] };
            },
            searchTerm: "",
            limit: 0,
          }),
          [],
        );
        assert.equal(captured.query.limit, 0);
        assert(Object.hasOwn(captured.query, "offset"));
        const empty = await model.readGroup({
          api: async () => ({}),
          groupId: "requested",
        });
        assert.equal(empty.username, null);
        assert.equal(empty.memberCount, 0);
        assert.equal(empty.activeCompetitionEntry, null);
        receipt.observations.push({
          name: "source zero/empty/nullish defaults, schema failures and exact opaque rejection identity",
          context: context.source,
          empty,
          explicitZeroForwarded: true,
          apiErrorIdentity: true,
        });
      }
      const model = createGroupSearchReadModel({
        ...ports,
        context: contract.contexts[0].source,
      });
      mode = "status";
      await assert.rejects(
        model.searchGroups({ api, searchTerm: "x" }),
        (e) => e === lastPortError && e.status === 503,
      );
      receipt.observations.push({
        name: "real local503 error from supplied API port propagates unchanged",
      });
      mode = "bad-json";
      await assert.rejects(
        model.readGroup({ api, groupId: "x" }),
        (e) => e === lastPortError && e instanceof SyntaxError,
      );
      receipt.observations.push({
        name: "real malformed local JSON API-port rejection propagates unchanged",
      });
      mode = "hold";
      const controller = new AbortController(),
        started = new Promise((r) => {
          heldResolve = r;
        });
      const pending = model.searchGroups({
        api,
        searchTerm: "held",
        signal: controller.signal,
      });
      const rejected = assert.rejects(
        pending,
        (e) => e === lastPortError && e.name === "AbortError",
      );
      await started;
      controller.abort();
      await rejected;
      receipt.observations.push({
        name: "native supplied signal reaches real held local read; no parent query-scheduler inference",
      });
      assert.equal(receipt.apiCalls.length, 13);
      assert.equal(receipt.requests.length, 13);
      assert(receipt.requests.every((r) => r.method === "GET"));
      receipt.pass = true;
    } catch (e) {
      receipt.failure = String(e.stack ?? e);
      throw e;
    } finally {
      server?.closeAllConnections();
      if (server) await new Promise((r) => server.close(r));
      if (output) {
        await mkdir(path.dirname(path.resolve(output)), { recursive: true });
        await writeFile(output, JSON.stringify(receipt, null, 2) + "\n");
      }
    }
  },
);
