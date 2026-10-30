import { isObservationInstant } from "../../lib/observation-time.mjs";
import { PublicKey } from "@solana/web3.js";
import contract from "./contract.json";
import type { StoredWalletRecord, WalletRecordSuccess } from "./types";

export const COUNTERS = [
  ["totalUnclaimedTokens", "Stored unclaimed-token counter"],
  ["totalClaimedTokens", "Stored claimed-token counter"],
  ["currentSolVolume", "Stored SOL-volume counter"],
  ["cashbackEarned", "Stored cashback-earned counter"],
  ["totalCashbackClaimed", "Stored cashback-claimed counter"],
  ["stableCashbackEarned", "Stored stable-cashback-earned counter"],
  ["totalStableCashbackClaimed", "Stored stable-cashback-claimed counter"],
] as const;
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
export function isWalletRecord(
  value: unknown,
  address: string,
): value is WalletRecordSuccess {
  if (
    !object(value) ||
    value.ok !== true ||
    value.address !== address ||
    value.programId !== contract.programId ||
    value.cluster !== "mainnet-beta" ||
    value.commitment !== "confirmed"
  )
    return false;
  try {
    const user = new PublicKey(address);
    const [pda] = PublicKey.findProgramAddressSync(
      [new TextEncoder().encode(contract.pdaSeed), user.toBytes()],
      new PublicKey(contract.programId),
    );
    if (user.toBase58() !== address || pda.toBase58() !== value.recordPda)
      return false;
  } catch {
    return false;
  }
  if (
    !Number.isSafeInteger(value.contextSlot) ||
    (value.contextSlot as number) < 0 ||
    typeof value.endpointHost !== "string" ||
    !/^[a-zA-Z0-9.-]{1,253}$/.test(value.endpointHost) ||
    !isObservationInstant(value.observedAt)
  )
    return false;
  if (value.record === null) return value.dataBytes === null;
  const r = value.record;
  return (
    Number.isSafeInteger(value.dataBytes) &&
    (value.dataBytes as number) >= contract.minimumBytes &&
    (value.dataBytes as number) <= 16_384 &&
    object(r) &&
    r.user === address &&
    typeof r.needsClaim === "boolean" &&
    typeof r.hasTotalClaimedTokens === "boolean" &&
    COUNTERS.every(([key]) => integer(r[key])) &&
    integer(r.lastUpdateTimestamp, true)
  );
}
export async function fetchWalletRecord(
  address: string,
  signal?: AbortSignal,
  fetcher: typeof fetch = fetch,
): Promise<WalletRecordSuccess> {
  signal?.throwIfAborted();
  const response = await fetcher(
    `/api/portfolio/pump-record?${new URLSearchParams({ address })}`,
    {
      method: "GET",
      credentials: "omit",
      cache: "no-store",
      headers: { Accept: "application/json" },
      signal,
    },
  );
  if (!response.ok)
    throw new Error("The public Pump record is unavailable or unsupported.");
  const value: unknown = await response.json();
  signal?.throwIfAborted();
  if (!isWalletRecord(value, address))
    throw new Error("The public Pump record is unavailable or unsupported.");
  return value;
}
export type { StoredWalletRecord };
