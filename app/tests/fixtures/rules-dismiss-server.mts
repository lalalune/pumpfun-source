/** Real existing native reads of the checked-in synthetic competition seed. */
import { buildApp } from "../../packages/backend/src/app.ts";
const key = `pf_live_${"A".repeat(49)}`; // Public synthetic fixture, not a credential.
if (process.env.PUMPFUN_DEVELOPER_API_KEY !== key)
  throw Error("Explicit fixture-only environment required");
const app = buildApp([]);
const ledger: Array<{
  method: string;
  path: string;
  keyMatched: boolean;
  status?: number;
}> = [];
const byId = new Map<string, (typeof ledger)[number]>();
app.addHook("onRequest", async (request) => {
  const entry = {
    method: request.method,
    path: request.url,
    keyMatched: request.headers.authorization === `Bearer ${key}`,
  };
  byId.set(request.id, entry);
  ledger.push(entry);
});
app.addHook("onResponse", async (request, reply) => {
  const entry = byId.get(request.id);
  if (entry) entry.status = reply.statusCode;
});
const url = await app.listen({ port: 0, host: "127.0.0.1" });
process.send?.({ event: "ready", url });
let closing = false;
async function close() {
  if (closing) return;
  closing = true;
  await app.close();
  process.exit(0);
}
process.on("message", (message: { id: number; command: string }) => {
  if (message.command === "snapshot")
    process.send?.({ id: message.id, ledger });
  else if (message.command === "close") void close();
  else throw Error("Unknown fixture command");
});
process.on("disconnect", () => void close());
process.on("SIGTERM", () => void close());
