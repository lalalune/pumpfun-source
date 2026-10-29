import { PublicKey } from "@solana/web3.js";
import { PUMP_SDK, userVolumeAccumulatorPda } from "@pump-fun/pump-sdk";
import {
  createPinnedRpcCall,
  PortfolioRpcError,
  type RpcCall,
} from "../portfolio/rpc";
import { MAINNET_GENESIS_HASH } from "../portfolio/types";
import contract from "./contract.json";
import type { StoredWalletRecord, WalletRecordSuccess } from "./types";

function invalid(): never {
  throw new PortfolioRpcError(
    "RPC_RESPONSE_INVALID",
    "The public Pump record was unavailable or unsupported.",
    false,
  );
}
function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    return invalid();
  return value as Record<string, unknown>;
}
export function walletKey(value: string): PublicKey {
  try {
    const key = new PublicKey(value);
    if (key.toBase58() !== value) throw new Error("noncanonical");
    return key;
  } catch {
    throw new PortfolioRpcError(
      "INVALID_ADDRESS",
      "Provide a canonical Solana public-key address.",
      false,
    );
  }
}
function decodeAccount(
  value: unknown,
  user: PublicKey,
): { record: StoredWalletRecord | null; dataBytes: number | null } {
  if (value === null) return { record: null, dataBytes: null };
  const a = object(value);
  if (
    a.owner !== contract.programId ||
    a.executable !== false ||
    !Number.isSafeInteger(a.lamports) ||
    (a.lamports as number) < 0
  )
    invalid();
  if (
    !Array.isArray(a.data) ||
    a.data.length !== 2 ||
    a.data[1] !== "base64" ||
    typeof a.data[0] !== "string" ||
    a.data[0].length > 22_000
  )
    invalid();
  const data = Buffer.from(a.data[0], "base64");
  if (
    data.toString("base64") !== a.data[0] ||
    data.length < contract.minimumBytes ||
    data.length > 16_384 ||
    !data.subarray(0, 8).equals(Buffer.from(contract.discriminator))
  )
    invalid();
  if (a.space !== undefined && a.space !== data.length) invalid();
  for (const f of contract.fields)
    if (f.type === "bool" && data[f.bytes[0]] > 1) invalid();
  let decoded;
  try {
    decoded = PUMP_SDK.decodeUserVolumeAccumulator({
      data,
      owner: new PublicKey(contract.programId),
      executable: false,
      lamports: a.lamports as number,
    });
  } catch {
    return invalid();
  }
  if (!decoded.user.equals(user)) invalid();
  const record: StoredWalletRecord = {
    user: decoded.user.toBase58(),
    needsClaim: decoded.needsClaim,
    hasTotalClaimedTokens: decoded.hasTotalClaimedTokens,
    totalUnclaimedTokens: decoded.totalUnclaimedTokens.toString(10),
    totalClaimedTokens: decoded.totalClaimedTokens.toString(10),
    currentSolVolume: decoded.currentSolVolume.toString(10),
    lastUpdateTimestamp: decoded.lastUpdateTimestamp.toString(10),
    cashbackEarned: decoded.cashbackEarned.toString(10),
    totalCashbackClaimed: decoded.totalCashbackClaimed.toString(10),
    stableCashbackEarned: decoded.stableCashbackEarned.toString(10),
    totalStableCashbackClaimed: decoded.totalStableCashbackClaimed.toString(10),
  };
  return { record, dataBytes: data.length };
}
export async function readWalletRecordWithRpc(
  address: string,
  call: RpcCall,
  endpointHost: string,
  signal?: AbortSignal,
): Promise<WalletRecordSuccess> {
  const user = walletKey(address),
    recordPda = userVolumeAccumulatorPda(user).toBase58();
  if (signal?.aborted) throw signal.reason;
  const genesis = await call("getGenesisHash", [], signal);
  if (signal?.aborted) throw signal.reason;
  if (genesis !== MAINNET_GENESIS_HASH)
    throw new PortfolioRpcError(
      "WRONG_CLUSTER",
      "The configured provider is not Solana mainnet.",
      false,
    );
  const response = object(
    await call(
      "getAccountInfo",
      [recordPda, { encoding: "base64", commitment: "confirmed" }],
      signal,
    ),
  );
  if (signal?.aborted) throw signal.reason;
  const context = object(response.context);
  if (
    !Number.isSafeInteger(context.slot) ||
    (context.slot as number) < 0 ||
    !Object.hasOwn(response, "value")
  )
    invalid();
  return {
    ok: true,
    address,
    programId: contract.programId,
    recordPda,
    cluster: "mainnet-beta",
    commitment: "confirmed",
    contextSlot: context.slot as number,
    endpointHost,
    observedAt: new Date().toISOString(),
    ...decodeAccount(response.value, user),
  };
}
export async function readLiveWalletRecord(
  address: string,
  options: { signal?: AbortSignal } = {},
) {
  walletKey(address);
  const { call, endpointHost } = await createPinnedRpcCall(
    process.env.SOLANA_RPC_URL,
    12_000,
    options.signal,
  );
  return readWalletRecordWithRpc(address, call, endpointHost, options.signal);
}
