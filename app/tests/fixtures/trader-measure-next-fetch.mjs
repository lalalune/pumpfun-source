// Test-only capability: redirect exactly the documented developer read to the
// owned loopback native fixture. Preserve path/query/method/headers/body/signal.
const target = new URL(process.env.PUMP_TEST_UPSTREAM_URL ?? "");
if (
  target.protocol !== "http:" ||
  target.hostname !== "127.0.0.1" ||
  !target.port ||
  target.pathname !== "/" ||
  target.search ||
  target.hash ||
  target.username ||
  target.password
)
  throw new Error("Explicit owned loopback upstream required");
const nativeFetch = globalThis.fetch;
globalThis.fetch = (input, init) => {
  const original = input instanceof Request ? input.url : String(input),
    url = new URL(original);
  if (url.origin === "https://api.pump.fun") {
    if (url.pathname !== "/v1/pnl-leaderboard")
      throw new Error("Unexpected developer operation in fixture");
    const local = new URL(url.pathname + url.search, target);
    return nativeFetch(
      input instanceof Request ? new Request(local, input) : local,
      init,
    );
  }
  if (url.hostname !== "127.0.0.1" && url.hostname !== "localhost")
    throw new Error("External fetch blocked in finite fixture");
  return nativeFetch(input, init);
};
