// Test-only native transport capability, adapted from the qualified #1600 driver.
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
  throw new Error("Explicit owned loopback fixture required");
const paths = new Set([
  "/v1/competitions",
  "/v1/competitions/synthetic-refresh",
]);
const nativeFetch = globalThis.fetch;
globalThis.fetch = (input, init) => {
  const original = input instanceof Request ? input.url : String(input),
    url = new URL(original);
  if (url.origin === "https://api.pump.fun") {
    if (!paths.has(url.pathname))
      throw new Error("Unexpected developer operation");
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
