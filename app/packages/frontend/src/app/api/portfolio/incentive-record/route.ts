import { handleGlobalIncentiveRecord } from "../../../global-incentive-record/handler";
export const runtime = "nodejs";
export function GET(request: Request) {
  return handleGlobalIncentiveRecord(request);
}
export function HEAD(request: Request) {
  return handleGlobalIncentiveRecord(request);
}
