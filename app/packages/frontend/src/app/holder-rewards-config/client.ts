import { isObservationInstant } from "../../lib/observation-time.mjs";
import { PublicKey } from "@solana/web3.js";
import contract from "./contract.json";
import type { HolderConfiguration } from "./types";
const record = (value: unknown): value is Record<string, unknown> =>
  value !== null && typeof value === "object" && !Array.isArray(value);
const integer = (value: unknown): value is number =>
  typeof value === "number" && Number.isSafeInteger(value) && value >= 0;
function key(value: unknown): value is string {
  if (typeof value !== "string" || value.length < 32 || value.length > 44)
    return false;
  try {
    return new PublicKey(value).toBase58() === value;
  } catch {
    return false;
  }
}
function field(
  value: unknown,
  dataBytes: number,
  end: number,
  kind: "boolean" | "key",
) {
  return dataBytes < end
    ? value === null
    : kind === "boolean"
      ? typeof value === "boolean"
      : key(value);
}
export function isHolderConfiguration(
  value: unknown,
  mint: string,
  rewardsPda: string,
): value is HolderConfiguration {
  if (
    !record(value) ||
    value.ok !== true ||
    value.mint !== mint ||
    value.holderRewardsPda !== rewardsPda ||
    value.programId !== contract.programId ||
    value.globalPda !== contract.globalPda ||
    !key(value.curvePda) ||
    value.cluster !== "mainnet-beta" ||
    value.commitment !== "confirmed" ||
    !integer(value.contextSlot) ||
    !isObservationInstant(value.observedAt) ||
    typeof value.endpointHost !== "string" ||
    value.endpointHost.length > 253 ||
    !/^[A-Za-z0-9][A-Za-z0-9.-]*$/.test(value.endpointHost) ||
    !record(value.global) ||
    !record(value.curve)
  )
    return false;
  try {
    if (!key(mint) || !key(rewardsPda)) return false;
    const program = new PublicKey(contract.programId);
    const derive = (seed: string) =>
      PublicKey.findProgramAddressSync(
        [new TextEncoder().encode(seed), new PublicKey(mint).toBytes()],
        program,
      )[0].toBase58();
    if (
      value.curvePda !== derive("bonding-curve") ||
      rewardsPda !== derive("holder-rewards")
    )
      return false;
  } catch {
    return false;
  }
  const global = value.global,
    curve = value.curve;
  if (global.status === "missing") {
    if (
      global.dataBytes !== null ||
      global.isHolderRewardEnabled !== null ||
      global.holderRewardClaimAuthority !== null
    )
      return false;
  } else if (
    global.status !== "decoded" ||
    !integer(global.dataBytes) ||
    global.dataBytes < 8 ||
    global.dataBytes > 65_536 ||
    !field(
      global.isHolderRewardEnabled,
      global.dataBytes,
      contract.accounts.Global.fields.is_holder_reward_enabled[1],
      "boolean",
    ) ||
    !field(
      global.holderRewardClaimAuthority,
      global.dataBytes,
      contract.accounts.Global.fields.holder_reward_claim_authority[1],
      "key",
    )
  )
    return false;
  if (curve.status === "missing") {
    return (
      curve.dataBytes === null &&
      curve.isHolderReward === null &&
      curve.creator === null &&
      curve.creatorMatchesHolderRewardsPda === null
    );
  }
  return (
    curve.status === "decoded" &&
    integer(curve.dataBytes) &&
    curve.dataBytes >= 49 &&
    curve.dataBytes <= 65_536 &&
    field(
      curve.isHolderReward,
      curve.dataBytes,
      contract.accounts.BondingCurve.fields.is_holder_reward[1],
      "boolean",
    ) &&
    field(
      curve.creator,
      curve.dataBytes,
      contract.accounts.BondingCurve.fields.creator[1],
      "key",
    ) &&
    (curve.creator === null
      ? curve.creatorMatchesHolderRewardsPda === null
      : curve.creatorMatchesHolderRewardsPda === (curve.creator === rewardsPda))
  );
}
export async function readHolderConfiguration(
  mint: string,
  rewardsPda: string,
  signal: AbortSignal,
  transport: typeof fetch = fetch,
): Promise<HolderConfiguration> {
  signal.throwIfAborted();
  const response = await transport(
    `/api/holder-rewards/configuration?${new URLSearchParams({ mint })}`,
    {
      method: "GET",
      credentials: "omit",
      cache: "no-store",
      headers: { Accept: "application/json" },
      signal,
    },
  );
  signal.throwIfAborted();
  const payload: unknown = await response.json();
  signal.throwIfAborted();
  if (!response.ok || !isHolderConfiguration(payload, mint, rewardsPda))
    throw new Error(
      "Public configuration is unavailable or unsupported. No eligibility is inferred.",
    );
  return payload;
}
