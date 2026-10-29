// Isolated GET-only input to the maintained Home Feed loader. Not a product API.
import { createServer } from "node:http";
const requests = [];
const timestamp =
  process.env.RELATIVE_TIME_FIXTURE_TIMESTAMP ??
  new Date(Date.now() - 20000).toISOString();
if (
  !Number.isFinite(Date.parse(timestamp)) ||
  new Date(timestamp).toISOString() !== timestamp
)
  throw Error("Fixture timestamp must be canonical ISO data");
const coin = {
  coinMint: "LOCAL_CLOCK_EXAMPLE",
  coinName: "Synthetic clock example",
  coinImage: null,
  symbol: "LOCAL",
  marketCap: 125000,
  chain: "solana",
  position: {
    userId: "local-clock-author",
    userName: "Local Clock Author",
    profileImage: null,
    walletAddress: null,
    isVerified: false,
    verifiedBadgeVisible: false,
    costBasisUsd: 2500,
    contentKind: "callout",
    callout: {
      calloutId: "00000000-0000-4000-8000-000000000002",
      chain: "solana",
      assetClass: "ASSET_CLASS_TOKEN",
      calledOutAtMcap: 100000,
      multiple: 1.25,
      thesis: "Synthetic timestamp sampled in the isolated read fixture.",
      mediaUrl: null,
      calloutTimestamp: timestamp,
    },
  },
};
const server = createServer((request, response) => {
  const url = new URL(request.url, "http://127.0.0.1:3001");
  const send = (status, body) => {
    response.writeHead(status, {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-reconstruction-data-source": "synthetic-home-feed-local-v1",
      "x-reconstruction-compatibility": "local-unqualified",
    });
    response.end(JSON.stringify(body));
  };
  if (request.method !== "GET")
    return send(405, { error: "READ_ONLY_TEST_INPUT" });
  if (url.pathname === "/__health") return send(200, { ok: true });
  if (url.pathname === "/__requests") return send(200, { requests, timestamp });
  requests.push(`${request.method} ${url.pathname}${url.search}`);
  process.stdout.write(`${requests.at(-1)}\n`);
  if (
    url.pathname === "/services/frontend/home-feed" &&
    url.search === "?pageSize=3"
  )
    return send(200, { coins: [coin] });
  return send(404, { error: "NOT_FOUND" });
});
server.listen(3001, "127.0.0.1", () =>
  process.stdout.write("Relative-time input on127.0.0.1:3001\n"),
);
for (const signal of ["SIGTERM", "SIGINT"])
  process.on(signal, () => server.close(() => process.exit(0)));
