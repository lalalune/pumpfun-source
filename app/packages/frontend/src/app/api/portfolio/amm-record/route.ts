import "server-only";
import { handleAmmWalletRecord } from "../../../amm-wallet-record/handler";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export async function GET(request: Request): Promise<Response> {
  return handleAmmWalletRecord(request);
}
