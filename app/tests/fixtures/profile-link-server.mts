// Loopback test infrastructure adapted from the prior selected-measure packet; no original-source recovery credit.
/** Owned loopback fixture; actual native backend and actual exported app adapter. */
import { createServer } from "node:http";
import { createInterface } from "node:readline";
import { buildApp } from "../../packages/backend/src/app.ts";
import {
  LeaderboardStore,
  type RawLeaderboardEntry,
} from "../../packages/backend/src/leaderboard-store.ts";
import { UserStore } from "../../packages/backend/src/users-store.ts";
import { createRequire } from "node:module";
const { GET } = createRequire(import.meta.url)(
  "../../packages/frontend/src/app/api/leaderboard/route.ts",
) as typeof import("../../packages/frontend/src/app/api/leaderboard/route.ts");

const fixtureKey = `pf_live_${"A".repeat(49)}`; // Existing public test-key format, not a credential.
if (process.env.PUMPFUN_DEVELOPER_API_KEY !== fixtureKey)
  throw new Error("Fixture-only environment required");
const wallets = [
  "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
  "DfMxre4cKmvogbLrPigxmibVTTQDuzjdXojWzjCXXhzj",
  "11111111111111111111111111111112",
];
const rows: RawLeaderboardEntry[] = wallets.map((walletAddress, i) => ({
  userId: i < 2 ? "user-001" : null,
  walletAddress,
  pnlSol: i ? 0.5 : 1,
  pnlUsd: i ? 50 / i : 100,
  pnlPercent: i ? 5 : 10,
  realizedPnlSol: i ? 0.4 : -0.2,
  realizedPnlUsd: i ? 40 : -20,
  unrealizedPnlSol: i ? 0.1 : 1.2,
  unrealizedPnlUsd: i ? 10 : 120,
  buySpendSol: 10,
  lastRefreshedAtMs: 1_759_200_000_000,
  positions: [],
}));
const ledger: Array<{
  generation: number;
  requestId: string;
  method: string;
  path: string;
  keyMatched: boolean;
  status?: number;
}> = [];
let backend: ReturnType<typeof buildApp> | undefined;
let backendPort = 0;
let generation = 0;
async function startBackend() {
  if (backend) throw new Error("Backend already running");
  const users = new UserStore();
  const store = new LeaderboardStore(
    { daily: rows, weekly: rows, monthly: rows },
    users,
  );
  const app = buildApp([], { userStore: users, leaderboardStore: store });
  const ownGeneration = ++generation;
  const observed = new Map<string, (typeof ledger)[number]>();
  app.addHook("onRequest", async (request) => {
    const row = {
      generation: ownGeneration,
      requestId: request.id,
      method: request.method,
      path: request.url,
      keyMatched: request.headers.authorization === `Bearer ${fixtureKey}`,
    };
    ledger.push(row);
    observed.set(request.id, row);
  });
  app.addHook("onResponse", async (request, reply) => {
    const row = observed.get(request.id);
    if (row) row.status = reply.statusCode;
  });
  const address = await app.listen({ port: backendPort, host: "127.0.0.1" });
  backendPort = Number(new URL(address).port);
  backend = app;
}
await startBackend();
const nativeFetch = globalThis.fetch;
globalThis.fetch = (input, init) => {
  const original = input instanceof Request ? input.url : String(input);
  const url = new URL(original);
  if (
    url.origin !== "https://api.pump.fun" ||
    url.pathname !== "/v1/pnl-leaderboard"
  )
    throw new Error("Unpermitted fixture upstream");
  const target = new URL(
    url.pathname + url.search,
    `http://127.0.0.1:${backendPort}`,
  );
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
  throw new Error("Loopback address required");
const send = (data: object) =>
  process.stdout.write(JSON.stringify(data) + "\n");
send({
  event: "ready",
  backendUrl: `http://127.0.0.1:${backendPort}`,
  adapterUrl: `http://127.0.0.1:${address.port}`,
  wallets,
});
let serial = Promise.resolve();
const lines = createInterface({ input: process.stdin });
lines.on("line", (line) => {
  serial = serial
    .then(async () => {
      const message = JSON.parse(line);
      if (message.command === "stop-backend") {
        await backend?.close();
        backend = undefined;
      } else if (message.command === "start-backend") await startBackend();
      else if (message.command === "snapshot") {
        send({ id: message.id, ledger });
        return;
      } else if (message.command === "close") {
        await backend?.close();
        await new Promise<void>((resolve) => gateway.close(() => resolve()));
        process.stdout.write(
          JSON.stringify({ id: message.id, ok: true }) + "\n",
          () => process.exit(0),
        );
        return;
      } else throw new Error("Unknown fixture command");
      send({ id: message.id, ok: true });
    })
    .catch(() => {
      send({ event: "error" });
      process.exitCode = 1;
    });
});

let terminating = false;
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
