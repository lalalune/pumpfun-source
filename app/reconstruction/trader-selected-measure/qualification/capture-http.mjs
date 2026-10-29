// Finite synthetic local read proof. Does not read a real credential or call a live API.
import assert from "node:assert/strict";
import { startTraderMeasureHttp } from "../../../tests/fixtures/trader-measure-http.mjs";

const fixture = await startTraderMeasureHttp();
const reads = [];
async function read(label, url) {
  const response = await fetch(url);
  const body = await response.json();
  reads.push({ label, status: response.status, cacheControl: response.headers.get("cache-control"), body });
  return reads.at(-1);
}
try {
  assert.equal((await read("direct handler without key", fixture.backendUrl + "/v1/pnl-leaderboard?period=daily")).status, 401);
  for (const sort of ["combined", "realized", "unrealized"]) {
    const result = await read(sort, fixture.adapterUrl + "/api/leaderboard?category=traders&period=daily&sort=" + sort);
    assert.equal(result.status, 200);
    assert.equal(result.body.data.kind, "traders");
    assert.equal(result.body.data.entries.length, 2);
  }
  const beforeInvalid = (await fixture.command("snapshot")).ledger.length;
  assert.equal((await read("invalid filter", fixture.adapterUrl + "/api/leaderboard?category=traders&sort=invalid")).status, 400);
  assert.equal((await fixture.command("snapshot")).ledger.length, beforeInvalid);
  await fixture.command("stop-backend");
  assert.equal((await read("genuine stopped backend", fixture.adapterUrl + "/api/leaderboard?category=traders&sort=realized")).status, 502);
  await fixture.command("start-backend");
  assert.equal((await read("restarted backend", fixture.adapterUrl + "/api/leaderboard?category=traders&sort=realized")).status, 200);
  const { ledger } = await fixture.command("snapshot");
  await fixture.close();
  process.stdout.write(JSON.stringify({ provenance: "Hand-authored synthetic facts, actual maintained Fastify handler and actual exported Next GET through a loopback HTTP bridge; this receipt is separate from the actual Next browser run", reads, ledger, fixtureExitCode: 0 }, null, 2) + "\n");
} catch (error) {
  await fixture.close();
  throw error;
}
