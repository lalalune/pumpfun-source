// Local implementation of the captured668487 GET read contract. The original
// server's internal implementation is not recoverable from its frontend client.
export const dynamic = "force-dynamic";

export function GET() {
  return Response.json(
    { nowMs: Date.now() },
    { headers: { "Cache-Control": "no-store" } },
  );
}
