// Finite synthetic native-read fixture. No public mutation endpoint or real key.
import { createServer } from "node:http";
import { createInterface } from "node:readline";
import { createRequire } from "node:module";
import { buildApp } from "../../packages/backend/src/app.ts";
import {
  CompetitionStore,
  type RawCompetition,
} from "../../packages/backend/src/competitions-store.ts";
import { UserStore } from "../../packages/backend/src/users-store.ts";
const { GET } = createRequire(import.meta.url)(
  "../../packages/frontend/src/app/api/leaderboard/route.ts",
) as typeof import("../../packages/frontend/src/app/api/leaderboard/route.ts");
const fixtureKey = `pf_live_${"A".repeat(49)}`;
if (process.env.PUMPFUN_DEVELOPER_API_KEY !== fixtureKey)
  throw new Error("Explicit fixture environment required");
const slug = "synthetic-refresh";
const wallet = "11111111111111111111111111111112";
let version = 1;
function seed(): RawCompetition[] {
  return [
    {
      id: "11111111-1111-4000-8000-000000000091",
      slug,
      kind: "person",
      title: `Synthetic read snapshot ${version}`,
      description:
        "Explicit synthetic facts; no production competition or calculated phase",
      prizeCopy: "No supplied prizes",
      imageUrl: null,
      prizes: [],
      registrationOpensAt: "2026-01-01T00:00:00.000Z",
      registrationClosesAt: "2026-01-02T00:00:00.000Z",
      startsAt: "2026-01-03T00:00:00.000Z",
      endsAt: "2030-01-04T00:00:00.000Z",
      minMembers: 1,
      maxMembers: 1,
      maxEntries: 10,
      phase: "live",
      isFinal: false,
      joinable: false,
      entries: [
        {
          entryId: "22222222-2222-4000-8000-000000000091",
          participantId: "33333333-3333-4000-8000-000000000091",
          walletAddress: wallet,
          registeredAt: "2026-01-01T12:00:00.000Z",
          struck: false,
          pnlUsd: version * 100,
          realizedPnlUsd: version * 60,
          unrealizedPnlUsd: version * 40,
          buySpendSol: 10,
          membersFresh: 1,
          lastRefreshedAtMs: 1_780_000_000_000 + version,
          positions: [],
          members: [],
        },
      ],
    },
  ];
}
type Observed = {
  generation: number;
  version: number;
  requestId: string;
  method: string;
  path: string;
  startedAtMs: number;
  completedAtMs?: number;
  keyMatched: boolean;
  status?: number;
};
const ledger: Observed[] = [];
let backend: ReturnType<typeof buildApp> | undefined,
  port = 0,
  generation = 0;
async function startBackend() {
  if (backend) throw new Error("Already running");
  const users = new UserStore([]),
    store = new CompetitionStore(seed(), users);
  const app = buildApp([], { userStore: users, competitionStore: store });
  const ownGeneration = ++generation,
    ownVersion = version,
    requests = new Map<string, Observed>();
  app.addHook("onRequest", async (request) => {
    const row: Observed = {
      generation: ownGeneration,
      version: ownVersion,
      requestId: request.id,
      method: request.method,
      path: request.url,
      startedAtMs: Date.now(),
      keyMatched: request.headers.authorization === `Bearer ${fixtureKey}`,
    };
    ledger.push(row);
    requests.set(request.id, row);
  });
  app.addHook("onResponse", async (request, reply) => {
    const row = requests.get(request.id);
    if (row) {
      row.status = reply.statusCode;
      row.completedAtMs = Date.now();
    }
  });
  const address = await app.listen({ host: "127.0.0.1", port });
  port = Number(new URL(address).port);
  backend = app;
}
await startBackend();
const nativeFetch = globalThis.fetch;
const paths = new Set(["/v1/competitions", "/v1/competitions/" + slug]);
globalThis.fetch = (input, init) => {
  const original = input instanceof Request ? input.url : String(input),
    url = new URL(original);
  if (url.origin !== "https://api.pump.fun" || !paths.has(url.pathname))
    throw new Error("Unpermitted fixture upstream");
  const target = new URL(url.pathname + url.search, `http://127.0.0.1:${port}`);
  return nativeFetch(
    input instanceof Request ? new Request(target, input) : target,
    init,
  );
};
const gateway = createServer(async (request, response) => {
  const url = new URL(request.url ?? "/", "http://127.0.0.1");
  if (request.method !== "GET" || url.pathname !== "/api/leaderboard") {
    response.writeHead(404).end();
    return;
  }
  try {
    const result = await GET(new Request(url));
    response.writeHead(result.status, Object.fromEntries(result.headers));
    response.end(Buffer.from(await result.arrayBuffer()));
  } catch {
    response.writeHead(500).end("Fixture bridge failed");
  }
});
await new Promise<void>((resolve) => gateway.listen(0, "127.0.0.1", resolve));
const address = gateway.address();
if (!address || typeof address === "string")
  throw new Error("Owned address required");
const send = (message: object) =>
  process.stdout.write(JSON.stringify(message) + "\n");
send({
  event: "ready",
  backendUrl: `http://127.0.0.1:${port}`,
  adapterUrl: `http://127.0.0.1:${address.port}`,
  slug,
  wallet,
});
let serial = Promise.resolve(),
  terminating = false;
const lines = createInterface({ input: process.stdin });
lines.on("line", (line) => {
  serial = serial
    .then(async () => {
      const message = JSON.parse(line);
      if (message.command === "snapshot") {
        send({ id: message.id, version, ledger });
        return;
      }
      if (message.command === "stop-backend") {
        await backend?.close();
        backend = undefined;
      } else if (message.command === "start-backend") await startBackend();
      else if (message.command === "advance" || message.command === "reset") {
        await backend?.close();
        backend = undefined;
        version = message.command === "reset" ? 1 : version + 1;
        await startBackend();
      } else if (message.command === "close") {
        await backend?.close();
        await new Promise<void>((resolve) => gateway.close(() => resolve()));
        process.stdout.write(
          JSON.stringify({ id: message.id, ok: true }) + "\n",
          () => process.exit(0),
        );
        return;
      } else throw new Error("Unknown fixture command");
      send({ id: message.id, ok: true, version });
    })
    .catch(() => {
      send({ event: "error" });
      process.exitCode = 1;
    });
});
async function terminate() {
  if (terminating) return;
  terminating = true;
  await backend?.close();
  gateway.close(() => process.exit(0));
}
lines.on("close", () => {
  void terminate();
});
process.on("SIGTERM", () => {
  void terminate();
});
