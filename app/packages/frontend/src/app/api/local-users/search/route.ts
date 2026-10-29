import { localUserSearchResponse } from "@/lib/local-user-search-server";

export const runtime = "nodejs";

export async function GET(request: Request) {
  return localUserSearchResponse(request);
}
