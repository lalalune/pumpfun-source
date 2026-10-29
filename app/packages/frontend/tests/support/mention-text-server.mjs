// Isolated synthetic read-only HTTP input for the actual Home Feed server path.
// Not imported by the backend, shipped as a route, or used as a production oracle.
import { createServer } from "node:http";
const host = "127.0.0.1",
  port = 3001;
const requests = [];
const id = "12345678-1234-1234-1234-123456789abc";
const content = `> Hello @[Alice](${id}). See https://x.com/reporter/status/12345?local=1!! Literal <script>window.mentionInjected=true</script> & malformed @[bad](not-an-id). https://evilx.com/a/status/9 stays text. https://twitter.com/${"long_username_".repeat(12)}/status/987654321.`;
const coin = {
  coinMint: "LOCAL_MENTION_EXAMPLE",
  coinName: "Synthetic rich content",
  coinImage: null,
  symbol: "LOCAL",
  marketCap: 125000,
  chain: "solana",
  position: {
    userId: "local-example-author",
    userName: "Local Example Author",
    profileImage: null,
    walletAddress: null,
    isVerified: false,
    verifiedBadgeVisible: false,
    costBasisUsd: 2500,
    contentKind: "callout",
    callout: {
      calloutId: "00000000-0000-4000-8000-000000000001",
      chain: "solana",
      assetClass: "ASSET_CLASS_TOKEN",
      calledOutAtMcap: 100000,
      multiple: 1.25,
      thesis: content,
      mediaUrl: null,
      calloutTimestamp: "2026-10-28T11:55:00.000Z",
    },
  },
};
const server = createServer((request, response) => {
  const url = new URL(request.url, `http://${host}:${port}`);
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
  if (url.pathname === "/__requests") return send(200, { requests });
  requests.push(`${request.method} ${url.pathname}${url.search}`);
  process.stdout.write(`${requests.at(-1)}\n`);
  if (
    url.pathname === "/services/frontend/home-feed" &&
    url.searchParams.get("pageSize") === "3"
  )
    return send(200, { coins: [coin] });
  return send(404, { error: "NOT_FOUND" });
});
server.listen(port, host, () =>
  process.stdout.write(`Mention text input on ${host}:${port}\n`),
);
for (const signal of ["SIGINT", "SIGTERM"])
  process.on(signal, () => server.close(() => process.exit(0)));
