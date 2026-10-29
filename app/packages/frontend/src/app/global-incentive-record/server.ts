import { PUMP_SDK, GLOBAL_VOLUME_ACCUMULATOR_PDA } from "@pump-fun/pump-sdk";
import { PublicKey } from "@solana/web3.js";
import {
  createPinnedRpcCall,
  PortfolioRpcError,
  type RpcCall,
} from "../portfolio/rpc";
import { MAINNET_GENESIS_HASH } from "../portfolio/types";
import contract from "./contract.json";
import type { GlobalIncentiveRecord, StoredIncentiveSchedule } from "./types";

function invalid(): never {
  throw new PortfolioRpcError(
    "RPC_RESPONSE_INVALID",
    "The public incentive record was unavailable or unsupported.",
    false,
  );
}
function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    return invalid();
  return value as Record<string, unknown>;
}
function decode(
  value: unknown,
): Pick<GlobalIncentiveRecord, "record" | "dataBytes"> {
  if (value === null) return { record: null, dataBytes: null };
  const account = object(value);
  if (
    account.owner !== contract.programId ||
    account.executable !== false ||
    !Number.isSafeInteger(account.lamports) ||
    (account.lamports as number) < 0 ||
    !Array.isArray(account.data) ||
    account.data.length !== 2 ||
    account.data[1] !== "base64" ||
    typeof account.data[0] !== "string" ||
    account.data[0].length > 22_000
  )
    invalid();
  const data = Buffer.from(account.data[0], "base64");
  if (
    data.toString("base64") !== account.data[0] ||
    data.length < contract.minimumBytes ||
    data.length > 16_384 ||
    !data.subarray(0, 8).equals(Buffer.from(contract.discriminator)) ||
    (account.space !== undefined && account.space !== data.length)
  )
    invalid();
  try {
    const decoded = PUMP_SDK.decodeGlobalVolumeAccumulator({
      data,
      owner: new PublicKey(contract.programId),
      executable: false,
      lamports: account.lamports as number,
    });
    if (
      decoded.totalTokenSupply.length !== 30 ||
      decoded.solVolumes.length !== 30
    )
      return invalid();
    const record: StoredIncentiveSchedule = {
      startTime: decoded.startTime.toString(10),
      endTime: decoded.endTime.toString(10),
      secondsInADay: decoded.secondsInADay.toString(10),
      mint: decoded.mint.toBase58(),
      totalTokenSupply: decoded.totalTokenSupply.map((value) =>
        value.toString(10),
      ),
      solVolumes: decoded.solVolumes.map((value) => value.toString(10)),
    };
    return { record, dataBytes: data.length };
  } catch {
    return invalid();
  }
}

export async function readGlobalIncentiveRecordWithRpc(
  call: RpcCall,
  endpointHost: string,
  signal?: AbortSignal,
): Promise<GlobalIncentiveRecord> {
  if (GLOBAL_VOLUME_ACCUMULATOR_PDA.toBase58() !== contract.recordPda)
    invalid();
  signal?.throwIfAborted();
  const genesis = await call("getGenesisHash", [], signal);
  signal?.throwIfAborted();
  if (genesis !== MAINNET_GENESIS_HASH)
    throw new PortfolioRpcError(
      "WRONG_CLUSTER",
      "The configured provider is not Solana mainnet.",
      false,
    );
  const response = object(
    await call(
      "getAccountInfo",
      [contract.recordPda, { encoding: "base64", commitment: "confirmed" }],
      signal,
    ),
  );
  signal?.throwIfAborted();
  const context = object(response.context);
  if (
    !Number.isSafeInteger(context.slot) ||
    (context.slot as number) < 0 ||
    !Object.hasOwn(response, "value")
  )
    invalid();
  return {
    ok: true,
    programId: contract.programId,
    recordPda: contract.recordPda,
    cluster: "mainnet-beta",
    commitment: "confirmed",
    contextSlot: context.slot as number,
    endpointHost,
    observedAt: new Date().toISOString(),
    ...decode(response.value),
  };
}

export async function readLiveGlobalIncentiveRecord(
  options: { signal?: AbortSignal } = {},
) {
  const { call, endpointHost } = await createPinnedRpcCall(
    process.env.SOLANA_RPC_URL,
    12_000,
  );
  return readGlobalIncentiveRecordWithRpc(call, endpointHost, options.signal);
}
