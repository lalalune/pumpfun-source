import { publicAddress } from "../auth/public-wallet/controller";
import contract from "./contract.json";
import type { GlobalIncentiveRecord } from "./types";

function object(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === "object" && !Array.isArray(value);
}
function integer(value: unknown, signed = false): value is string {
  if (
    typeof value !== "string" ||
    value.length > 20 ||
    !(signed ? /^(0|-?[1-9]\d*)$/ : /^(0|[1-9]\d*)$/).test(value)
  )
    return false;
  const n = BigInt(value);
  return signed ? n >= -(1n << 63n) && n < 1n << 63n : n < 1n << 64n;
}
export function isGlobalIncentiveRecord(
  value: unknown,
): value is GlobalIncentiveRecord {
  if (
    !object(value) ||
    value.ok !== true ||
    value.programId !== contract.programId ||
    value.recordPda !== contract.recordPda ||
    value.cluster !== "mainnet-beta" ||
    value.commitment !== "confirmed" ||
    !Number.isSafeInteger(value.contextSlot) ||
    (value.contextSlot as number) < 0 ||
    typeof value.endpointHost !== "string" ||
    !/^[a-zA-Z0-9.-]{1,253}$/.test(value.endpointHost) ||
    typeof value.observedAt !== "string" ||
    !Number.isFinite(Date.parse(value.observedAt))
  )
    return false;
  if (value.record === null) return value.dataBytes === null;
  if (
    !Number.isSafeInteger(value.dataBytes) ||
    (value.dataBytes as number) < contract.minimumBytes ||
    (value.dataBytes as number) > 16_384 ||
    !object(value.record)
  )
    return false;
  const r = value.record;
  try {
    publicAddress(r.mint);
  } catch {
    return false;
  }
  return (
    integer(r.startTime, true) &&
    integer(r.endTime, true) &&
    integer(r.secondsInADay, true) &&
    [r.totalTokenSupply, r.solVolumes].every(
      (array) =>
        Array.isArray(array) &&
        array.length === 30 &&
        array.every((value) => integer(value)),
    )
  );
}
export async function fetchGlobalIncentiveRecord(
  signal?: AbortSignal,
  fetcher: typeof fetch = fetch,
): Promise<GlobalIncentiveRecord> {
  signal?.throwIfAborted();
  const response = await fetcher("/api/portfolio/incentive-record", {
    method: "GET",
    credentials: "omit",
    cache: "no-store",
    headers: { Accept: "application/json" },
    signal,
  });
  if (!response.ok)
    throw new Error(
      "The public incentive record is unavailable or unsupported.",
    );
  const value: unknown = await response.json();
  signal?.throwIfAborted();
  if (!isGlobalIncentiveRecord(value))
    throw new Error(
      "The public incentive record is unavailable or unsupported.",
    );
  return value;
}
