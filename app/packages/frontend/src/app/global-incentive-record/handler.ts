import { PortfolioRpcError } from "../portfolio/rpc";
import { readLiveGlobalIncentiveRecord } from "./server";

export async function handleGlobalIncentiveRecord(
  request: Request,
  read = readLiveGlobalIncentiveRecord,
): Promise<Response> {
  const send = (value: unknown, status: number) =>
    new Response(request.method === "HEAD" ? null : JSON.stringify(value), {
      status,
      headers: {
        "Cache-Control": "no-store",
        "Content-Type": "application/json",
      },
    });
  const error = (status: number, code: string, retryable: boolean) =>
    send(
      {
        ok: false,
        error: {
          code,
          retryable,
          message: "The public incentive record is unavailable or unsupported.",
        },
      },
      status,
    );
  if (request.method !== "GET" && request.method !== "HEAD")
    return error(405, "METHOD_NOT_ALLOWED", false);
  if ([...new URL(request.url).searchParams].length)
    return error(400, "INVALID_QUERY", false);
  try {
    return send(await read({ signal: request.signal }), 200);
  } catch (e) {
    if (!(e instanceof PortfolioRpcError))
      return error(502, "RPC_UNAVAILABLE", true);
    const status =
      e.code === "RPC_RATE_LIMITED"
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
