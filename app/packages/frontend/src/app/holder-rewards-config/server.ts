import { Buffer } from "node:buffer";
import {
  PUMP_SDK,
  PUMP_PROGRAM_ID,
  GLOBAL_PDA,
  bondingCurvePda,
  holderRewardsPda,
} from "@pump-fun/pump-sdk";
import { PublicKey, type AccountInfo } from "@solana/web3.js";
import {
  createPinnedRpcCall,
  PortfolioRpcError,
  RPC_COMMITMENT,
  validateWalletAddress,
  type RpcCall,
} from "../portfolio/rpc";
import { MAINNET_GENESIS_HASH } from "../portfolio/types";
import contract from "./contract.json";
import type {
  HolderConfiguration,
  GlobalHolderConfiguration,
  CurveHolderConfiguration,
} from "./types";

function invalid(): never {
  throw new PortfolioRpcError(
    "RPC_RESPONSE_INVALID",
    "The Pump account response is invalid or uses an unsupported account layout.",
    false,
  );
}
function record(value: unknown): Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value))
    return invalid();
  return value as Record<string, unknown>;
}
function safeInteger(value: unknown): number {
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value < 0)
    return invalid();
  return value;
}
function account(
  value: unknown,
  discriminator: readonly number[],
): AccountInfo<Buffer> {
  const raw = record(value);
  if (
    raw.owner !== PUMP_PROGRAM_ID.toBase58() ||
    raw.executable !== false ||
    !Array.isArray(raw.data) ||
    raw.data.length !== 2 ||
    raw.data[1] !== "base64" ||
    typeof raw.data[0] !== "string" ||
    raw.data[0].length > 90_000 ||
    !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(
      raw.data[0],
    )
  )
    return invalid();
  const data = Buffer.from(raw.data[0], "base64");
  if (
    data.length > 65_536 ||
    data.toString("base64") !== raw.data[0] ||
    !data.subarray(0, 8).equals(Buffer.from(discriminator))
  )
    return invalid();
  if (raw.space !== undefined && safeInteger(raw.space) !== data.length)
    return invalid();
  // Public SDK AccountInfo uses numeric lamports, although this read never reports money.
  // Reject unsupported unsafe metadata rather than inventing or rounding it.
  const lamports =
    typeof raw.lamports === "string" && /^(0|[1-9]\d*)$/.test(raw.lamports)
      ? Number(raw.lamports)
      : raw.lamports;
  return {
    data,
    owner: new PublicKey(raw.owner),
    executable: false,
    lamports: safeInteger(lamports),
  };
}
function present(data: Buffer, range: readonly number[]): boolean {
  return data.length >= range[1];
}
function encodedBoolean(
  data: Buffer,
  range: readonly number[],
  decoded: unknown,
): boolean | null {
  if (!present(data, range)) return null;
  const encoded = data[range[0]];
  if ((encoded !== 0 && encoded !== 1) || decoded !== (encoded === 1))
    return invalid();
  return decoded as boolean;
}

/** Same declared SDK account pair, with explicit owner/discriminator/field-availability guards. */
export async function readHolderConfigurationWithRpc(
  mintInput: string,
  call: RpcCall,
  endpointHost: string,
  signal?: AbortSignal,
): Promise<HolderConfiguration> {
  const mint = new PublicKey(validateWalletAddress(mintInput));
  const curvePda = bondingCurvePda(mint),
    rewardsPda = holderRewardsPda(mint);
  signal?.throwIfAborted();
  const [genesis, result] = await Promise.all([
    call("getGenesisHash", [], signal),
    call(
      "getMultipleAccounts",
      [
        [GLOBAL_PDA.toBase58(), curvePda.toBase58()],
        { encoding: "base64", commitment: RPC_COMMITMENT },
      ],
      signal,
    ),
  ]);
  signal?.throwIfAborted();
  if (genesis !== MAINNET_GENESIS_HASH)
    throw new PortfolioRpcError(
      "WRONG_CLUSTER",
      "The configured public data source is not Solana mainnet-beta.",
      false,
    );
  const envelope = record(result),
    context = record(envelope.context),
    contextSlot = safeInteger(context.slot);
  if (!Array.isArray(envelope.value) || envelope.value.length !== 2)
    return invalid();
  let global: GlobalHolderConfiguration = {
    status: "missing",
    dataBytes: null,
    isHolderRewardEnabled: null,
    holderRewardClaimAuthority: null,
  };
  let curve: CurveHolderConfiguration = {
    status: "missing",
    dataBytes: null,
    isHolderReward: null,
    creator: null,
    creatorMatchesHolderRewardsPda: null,
  };
  try {
    if (envelope.value[0] !== null) {
      const info = account(
        envelope.value[0],
        contract.accounts.Global.discriminator,
      );
      const decoded = PUMP_SDK.decodeGlobal(info),
        fields = contract.accounts.Global.fields;
      global = {
        status: "decoded",
        dataBytes: info.data.length,
        isHolderRewardEnabled: encodedBoolean(
          info.data,
          fields.is_holder_reward_enabled,
          decoded.isHolderRewardEnabled,
        ),
        holderRewardClaimAuthority: present(
          info.data,
          fields.holder_reward_claim_authority,
        )
          ? decoded.holderRewardClaimAuthority.toBase58()
          : null,
      };
    }
    if (envelope.value[1] !== null) {
      const info = account(
        envelope.value[1],
        contract.accounts.BondingCurve.discriminator,
      );
      const decoded = PUMP_SDK.decodeBondingCurve(info),
        fields = contract.accounts.BondingCurve.fields;
      const creator = present(info.data, fields.creator)
        ? decoded.creator.toBase58()
        : null;
      curve = {
        status: "decoded",
        dataBytes: info.data.length,
        isHolderReward: encodedBoolean(
          info.data,
          fields.is_holder_reward,
          decoded.isHolderReward,
        ),
        creator,
        creatorMatchesHolderRewardsPda:
          creator === null ? null : creator === rewardsPda.toBase58(),
      };
    }
  } catch {
    return invalid();
  }
  return {
    ok: true,
    mint: mint.toBase58(),
    programId: PUMP_PROGRAM_ID.toBase58(),
    globalPda: GLOBAL_PDA.toBase58(),
    curvePda: curvePda.toBase58(),
    holderRewardsPda: rewardsPda.toBase58(),
    cluster: "mainnet-beta",
    commitment: RPC_COMMITMENT,
    contextSlot,
    observedAt: new Date().toISOString(),
    endpointHost,
    global,
    curve,
  };
}

export async function readLiveHolderConfiguration(
  mint: string,
  signal?: AbortSignal,
): Promise<HolderConfiguration> {
  const { call, endpointHost } = await createPinnedRpcCall(
    process.env.SOLANA_RPC_URL,
    10_000,
    signal,
  );
  return readHolderConfigurationWithRpc(mint, call, endpointHost, signal);
}
