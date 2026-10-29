import { PortfolioRpcError } from "../portfolio/rpc";
import { readLiveAmmWalletRecord } from "./server";

export async function handleAmmWalletRecord(
  request: Request,
  read = readLiveAmmWalletRecord,
): Promise<Response> {
  const headers = { "Cache-Control": "no-store" };
  const send = (value: unknown, status = 200) =>
    request.method === "HEAD"
      ? new Response(null, {
          status,
          headers: { ...headers, "Content-Type": "application/json" },
        })
      : Response.json(value, { status, headers });
  const error = (status: number, code: string, retryable: boolean) =>
    send(
      {
        ok: false,
        error: {
          code,
          retryable,
          message: "The public PumpSwap record is unavailable or unsupported.",
        },
      },
      status,
    );
  const query = new URL(request.url).searchParams;
  if (request.method !== "GET" && request.method !== "HEAD")
    return error(405, "METHOD_NOT_ALLOWED", false);
  if (
    query.getAll("address").length !== 1 ||
    [...query.keys()].some((key) => key !== "address")
  )
    return error(400, "INVALID_ADDRESS", false);
  try {
    return send(await read(query.get("address")!, { signal: request.signal }));
  } catch (e) {
    if (!(e instanceof PortfolioRpcError))
      return error(502, "RPC_UNAVAILABLE", true);
    const status =
      e.code === "INVALID_ADDRESS"
        ? 400
        : e.code === "RPC_RATE_LIMITED"
          ? 429
          : e.code === "RPC_TIMEOUT"
            ? 504
            : [
                  "RPC_CONFIGURATION_INVALID",
                  "RPC_DNS_REJECTED",
                  "WRONG_CLUSTER",
                ].includes(e.code)
              ? 503
              : 502;
    return error(status, e.code, e.retryable);
  }
}
