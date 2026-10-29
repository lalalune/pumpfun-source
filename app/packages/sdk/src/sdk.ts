import { AnchorProvider, Program } from "@coral-xyz/anchor";
import { PumpAgentOffline } from "@pump-fun/agent-payments-sdk";
import {
  ASSOCIATED_TOKEN_PROGRAM_ID,
  createAssociatedTokenAccountIdempotentInstruction,
  createCloseAccountInstruction,
  createSyncNativeInstruction,
  getAssociatedTokenAddressSync,
  NATIVE_MINT,
  TOKEN_2022_PROGRAM_ID,
  TOKEN_PROGRAM_ID,
} from "@solana/spl-token";
import {
  AccountInfo,
  AccountMeta,
  Connection,
  PublicKey,
  SystemProgram,
  TransactionInstruction,
} from "@solana/web3.js";
import BN from "bn.js";

import {
  getBuybackFeeRecipientForTokenQuote,
  getStaticRandomFeeRecipient,
  getStaticRandomFeeRecipientForBuyback,
} from "./bondingCurve";
import {
  NoShareholdersError,
  TooManyShareholdersError,
  ZeroShareError,
  InvalidShareTotalError,
  DuplicateShareholderError,
  CashbackDeprecatedError,
  CashbackCoinNotSupportedError,
  CreatorFeeBpsOutOfRangeError,
  CreatorFeeNotConfigurableError,
  HolderRewardDisabledError,
} from "./errors";
import { getFeeRecipient } from "./fees";
import { lessSlippage } from "./slippage";
import { Pump } from "./idl/pump";
import pumpIdl from "./idl/pump.json";
import { PumpAmm } from "./idl/pump_amm";
import PumpAmmIdl from "./idl/pump_amm.json";
import { PumpFees } from "./idl/pump_fees";
import PumpFeesIdl from "./idl/pump_fees.json";
import { OFFLINE_PUMP_PROGRAM } from "./onlineSdk";
import {
  ammCreatorVaultPda,
  bondingCurvePda,
  canonicalPumpPoolPda,
  creatorVaultPda,
  donationFeePda,
  donationRelayDebouncerPda,
  donationRelayEpochTrackerPda,
  donationRelayEventAuthorityPda,
  donationRelayMintWhitelistPda,
  getGlobalParamsPda,
  getMayhemStatePda,
  getSolVaultPda,
  getTokenVaultPda,
  pumpPoolAuthorityPda,
  feeSharingConfigPda,
  QUOTE_CONTROL_PDA,
  socialFeePda,
  userVolumeAccumulatorPda,
  bondingCurveV2Pda,
  quoteAta,
  boostVaultAuthorityPda,
  isLegacyQuoteMint,
  normalizeQuoteMint,
  getEventAuthorityPda,
  canonicalPumpPoolPdaWithQuote,
  holderRewardsPda,
  GLOBAL_PDA,
  PUMP_FEE_CONFIG_PDA,
  PUMP_EVENT_AUTHORITY_PDA,
  PUMP_AMM_EVENT_AUTHORITY_PDA,
  PUMP_FEE_EVENT_AUTHORITY_PDA,
} from "./pda";
import {
  AddQuoteControlMintEvent,
  AdminCtoEvent,
  AdminCtoPoolEventAmm,
  BondingCurve,
  BuyEventAmm,
  CollectCreatorFeeEventBc,
  CompleteEventBc,
  CreateEventBc,
  DonationFeePda as DonationFeePdaState,
  CreatePoolEventAmm,
  DepositEventAmm,
  FeeConfig,
  Fees,
  Global,
  GlobalVolumeAccumulator,
  QuoteControl,
  RemoveQuoteControlMintEvent,
  SetQuoteControlAdminEvent,
  PostCompleteBuyEvent,
  SweepBondingCurveFeeEvent,
  SweepPoolFeeEventAmm,
  TradeEventBc,
  UpdateCreatorFeeConfigEvent,
  UserVolumeAccumulator,
  Shareholder,
  SellEventAmm,
  SharingConfig,
  CollectCoinCreatorFeeEventAmm,
  ClaimCashbackEvent,
  DistributeCreatorFeesEvent,
  DistributeFeeToHoldersEvent,
  MinimumDistributableFeeEvent,
  SocialFeePda as SocialFeePdaState,
  SocialFeePdaClaimedEvent,
  SocialFeePdaCreatedEvent,
  WithdrawEventAmm,
  CreateFeeSharingConfigEvent,
  UpdateFeeSharesEvent,
  UpdateAdminEvent,
  SetAuthorityEvent,
  ResetFeeSharingConfigEvent,
  DonationFeePdaCreatedEvent,
} from "./state";
import {
  coinCreatorVaultAtaPda,
  coinCreatorVaultAuthorityPda,
  GLOBAL_CONFIG_PDA as AMM_GLOBAL_CONFIG_PDA,
} from "./swap/pda";

export function getPumpProgram(connection: Connection): Program<Pump> {
  return new Program(
    pumpIdl as Pump,
    new AnchorProvider(connection, null as any, {}),
  );
}

export const PUMP_PROGRAM_ID = new PublicKey(
  "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P",
);

export function getPumpAmmProgram(connection: Connection): Program<PumpAmm> {
  return new Program(
    PumpAmmIdl as PumpAmm,
    new AnchorProvider(connection, null as any, {}),
  );
}

export function getPumpFeeProgram(connection: Connection): Program<PumpFees> {
  return new Program(
    PumpFeesIdl as PumpFees,
    new AnchorProvider(connection, null as any, {}),
  );
}

export const PUMP_AMM_PROGRAM_ID = new PublicKey(
  "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA",
);

export const MAYHEM_PROGRAM_ID = new PublicKey(
  "MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e",
);

export const PUMP_FEE_PROGRAM_ID = new PublicKey(
  "pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ",
);

/**
 * `BondingCurve` serialized length with every field the vendored IDL declares
 * (pump `BondingCurve::SIZE`, discriminator included). Curves written before
 * the depth fields (`depth`, `initialVirtualQuoteReserves`, the
 * post-completion leg) are 141 bytes, before the v3 fee buckets 125, before
 * holder-reward coins 124, before
 * configurable creator fees 115 (or `BONDING_CURVE_NEW_SIZE` once extended);
 * the program reads them with the missing trailing fields at their defaults
 * (`creatorFeeBps = 0`, `canEditCreatorFee = false`, `isHolderReward = false`,
 * `creatorFee = protocolFees = 0`, `depth = 0`, the rest zero), which is what
 * zero-padding to this length yields. A trade, sweep or `extend_account`
 * grows a shorter curve to this length.
 */
export const BONDING_CURVE_SIZE = 166;
/** pump `BondingCurve::NEW_SIZE`: what `extend_account` grows a curve to. */
export const BONDING_CURVE_NEW_SIZE = 166;
// pump `BondingCurve::INITIALIZE_SIZE`, the shortest layout ever written; the
// program's reader rejects anything shorter.
const BONDING_CURVE_INITIALIZE_SIZE = 49;
/**
 * `Global` serialized length with every field the vendored IDL declares (pump
 * `Global::SIZE`, discriminator included). The account is 1054 bytes (1045
 * before configurable creator fees) until `extend_account` runs on it after
 * the holder-reward upgrade; zero-padding to this length reads the missing
 * fields at the program's defaults (`creatorFeeConfigurable = false`,
 * `maxConfigurableCreatorFeeBps = 0`, `holderRewardClaimAuthority` the zero
 * key, `isHolderRewardEnabled = false`, `maxCurveDepth = 0`). Until
 * `extend_account` grows the live 1087-byte account the upgraded program
 * refuses every instruction that reads `Global` (Anchor 3003).
 */
export const GLOBAL_SIZE = 1088;

/**
 * Compute units an `admin_cto` needs: a vault sweep plus up to two CPIs and an
 * ATA create overrun the 200k default. `OnlinePumpSdk.adminCtoInstructions`
 * prepends a `setComputeUnitLimit` with it.
 */
export const ADMIN_CTO_COMPUTE_UNIT_LIMIT = 600_000;

/**
 * `data` zero-padded to `size` bytes, or `data` itself when already that
 * long. Anchor account types decoded here have only ever gained trailing
 * fields, each defaulting to zero / `false`, so this reads an account written
 * under an older layout exactly as the program does.
 */
function zeroPadded(data: Buffer, size: number): Buffer {
  return data.length >= size
    ? data
    : Buffer.concat([data, Buffer.alloc(size - data.length)]);
}

// How many zero bytes make an older `CreateEvent` layout decode under the
// vendored one, tried in this order: none (the full layout), one (no
// `depth`: a zero u8), two (no `is_holder_reward` either: a `false`), ten (no
// `creator_fee_bps` either: a zero u64).
const CREATE_EVENT_LAYOUT_PADDINGS: readonly number[] = [0, 1, 2, 10];
// Likewise for the pump-amm `CreatePoolEvent`: none (the full layout), one
// (no `is_holder_reward`: a `false`) or ten (neither `creator_fee_bps` nor
// `can_edit_creator_fee` either, every event emitted before configurable
// creator fees: a zero u64 then two `false`).
const CREATE_POOL_EVENT_LAYOUT_PADDINGS: readonly number[] = [0, 1, 10];
// And for the trade events (pump `TradeEvent`, pump-amm `BuyEvent` /
// `SellEvent`): none, eight (no `quote_transfer_fee`, every event emitted
// before transfer-fee quotes: a zero u64), sixteen (no `creator_fee_unclaimed`
// either, every event emitted before the v3 / v2 fee buckets) or thirty-two
// (no `holder_rewards_bps` / `holder_rewards` either, every event emitted
// before holder-reward coins: four zero u64).
const TRADE_EVENT_LAYOUT_PADDINGS: readonly number[] = [0, 8, 16, 32];

// pump-amm `DepositEvent` / `WithdrawEvent` end with `quote_transfer_fee`
// (u64, pump-programs-monorepo #65); an event without it decodes it as zero.
const LIQUIDITY_EVENT_LAYOUT_PADDINGS: readonly number[] = [0, 8];

/**
 * `FeeConfig` account lengths, mirroring pump-fees
 * `FeeConfig::{INITIALIZE_SIZE, POST_STABLE_SIZE, CURRENT_SIZE}`. The program
 * selects the layout version from the account length: every version is a
 * prefix of the next and the fields a version lacks read as their defaults.
 */
export const FEE_CONFIG_INITIALIZE_SIZE = 2512;
export const FEE_CONFIG_POST_STABLE_SIZE = 4073;
export const FEE_CONFIG_CURRENT_SIZE = 4097;

// `FeeConfig` borsh layout: discriminator (8) + bump (1) + admin (32) +
// flat_fees (24), then `fee_tiers` and `stable_fee_tiers` (u32 length prefix +
// 40-byte tiers each), then exotic_flat_fees (24).
const FEE_CONFIG_FEE_TIERS_OFFSET = 8 + 1 + 32 + 24;
const FEE_TIER_LEN = 16 + 24;
const FEES_LEN = 24;
const VEC_LEN_PREFIX = 4;
// pump-fees `MAX_FEE_TIERS_SUPPORTED`: `upsert_fee_tiers` /
// `upsert_stable_fee_tiers` never write a longer vector, and the account sizes
// above are computed from it.
const MAX_FEE_TIERS_SUPPORTED = 50;

/**
 * End offset of the `Vec<FeeTier>` whose length prefix sits at `offset`,
 * rejecting a vector the program could not have written: longer than
 * `MAX_FEE_TIERS_SUPPORTED` or running past the data. Without the check a
 * corrupt length prefix would make the borsh coder allocate until the process
 * dies (a `FeeTier` holds no pubkey, so nothing in it ever throws).
 */
function feeTierVecEnd(data: Buffer, offset: number): number {
  const count = data.readUInt32LE(offset);
  const end = offset + VEC_LEN_PREFIX + count * FEE_TIER_LEN;
  if (count > MAX_FEE_TIERS_SUPPORTED || end > data.length) {
    throw new Error(
      `Invalid FeeConfig account: ${count} fee tiers declared at offset ${offset} in ${data.length} bytes`,
    );
  }
  return end;
}

// `QuoteControl` borsh layout: discriminator (8) + admin (32) + reserves_admin
// (32) + _reserved (32) + `mints` u32 length prefix (4) = 108 header bytes,
// then 40-byte entries (mint 32 + u64 initial_virtual_quote_reserves 8).
// Mirrors pump `QuoteControl::{HEADER_LEN, LEN_OFFSET, ENTRY_LEN}`.
const QUOTE_CONTROL_HEADER_LEN = 8 + 32 + 32 + 32 + VEC_LEN_PREFIX;
const QUOTE_CONTROL_LEN_OFFSET = QUOTE_CONTROL_HEADER_LEN - VEC_LEN_PREFIX;
const QUOTE_CONTROL_ENTRY_LEN = 32 + 8;

// Checked by name rather than `instanceof`: the error is raised by the
// buffer's realm, which is not ours under jest/vm.
function isRangeError(error: unknown): boolean {
  return (
    typeof error === "object" &&
    error !== null &&
    (error as { name?: unknown }).name === "RangeError"
  );
}

/**
 * Decodes an event whose layout has only ever gained trailing fields, each
 * defaulting to zero / `false`: `decode` is tried with each of `paddings`
 * zero bytes appended to `data`, shortest first, until the borsh coder stops
 * running out of bytes. Anything but a RangeError is rethrown at once; when
 * every padding runs out of bytes the event is truncated inside a field and
 * the last RangeError is thrown.
 */
function decodeWithTrailingDefaults<T>(
  data: Buffer,
  paddings: readonly number[],
  decode: (bytes: Buffer) => T,
): T {
  let rangeError: unknown;
  for (const padding of paddings) {
    try {
      return decode(Buffer.concat([data, Buffer.alloc(padding)]));
    } catch (error) {
      if (!isRangeError(error)) {
        throw error;
      }
      rangeError = error;
    }
  }
  throw rangeError;
}

/**
 * The `create_v2` rules the builders handed `Global` check up front
 * (`create_v2.rs`): 6082 `CashbackDeprecated` for any `cashback`, 6084
 * `HolderRewardDisabled` for `holderReward` while the gate is off, and for a
 * nonzero `creatorFeeBps` 6077 `CreatorFeeNotConfigurable` and 6078
 * `CreatorFeeBpsOutOfRange`. A zero or omitted rate means the schedule rate
 * and always passes. The quote rule for a rate (6091 on a SOL or whitelisted
 * quote at CTO time; ignored at create time) is left to the program.
 */
function assertCreateV2FlagsAllowed({
  global,
  mint,
  cashback,
  holderReward,
  creatorFeeBps,
}: {
  global: Global;
  mint: PublicKey;
  cashback: boolean | undefined;
  holderReward: boolean | undefined;
  creatorFeeBps: BN | undefined;
}): void {
  if (cashback) {
    throw new CashbackDeprecatedError(mint);
  }
  if (holderReward && !global.isHolderRewardEnabled) {
    throw new HolderRewardDisabledError();
  }
  if (!creatorFeeBps || creatorFeeBps.isZero()) {
    return;
  }
  if (!global.creatorFeeConfigurable) {
    throw new CreatorFeeNotConfigurableError();
  }
  if (
    creatorFeeBps.ltn(1) ||
    creatorFeeBps.gt(global.maxConfigurableCreatorFeeBps)
  ) {
    throw new CreatorFeeBpsOutOfRangeError(
      creatorFeeBps,
      global.maxConfigurableCreatorFeeBps,
    );
  }
}

/**
 * The key a coin's creator fees accrue to right after `create_v2`: the
 * holder-rewards PDA for a holder-reward coin (the program replaces the
 * `creator` argument with it), else the `creator` argument.
 */
function createdCurveCreator(
  mint: PublicKey,
  creator: PublicKey,
  holderReward: boolean | undefined,
): PublicKey {
  return holderReward ? holderRewardsPda(mint) : creator;
}

export const PUMP_TOKEN_MINT = new PublicKey(
  "pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn",
);

export const MAX_SHAREHOLDERS = 10;

const MIGRATE_FIXED_ACCOUNTS = 25;
const MIGRATE_V2_FIXED_ACCOUNTS = 27;
// `quote_mint`'s position in `MigrateV2`.
const MIGRATE_V2_QUOTE_MINT_INDEX = 3;

function assertBoostRemainingAccounts(
  instruction: TransactionInstruction,
  fixedAccounts: number,
  boostVaultAuthority: PublicKey,
  boostVault: PublicKey,
): void {
  const expectedLength = fixedAccounts + 2;
  if (instruction.keys.length !== expectedLength) {
    throw new Error(
      `migrate: expected ${expectedLength} accounts (${fixedAccounts} fixed + 2 boost), ` +
        `got ${instruction.keys.length}`,
    );
  }
  if (!instruction.keys[fixedAccounts].pubkey.equals(boostVaultAuthority)) {
    throw new Error(
      `migrate: boost_vault_authority expected at index ${fixedAccounts}`,
    );
  }
  if (!instruction.keys[fixedAccounts + 1].pubkey.equals(boostVault)) {
    throw new Error(
      `migrate: boost_vault expected at index ${fixedAccounts + 1}`,
    );
  }
}

/**
 * The `create_v2` remaining accounts that select a non-SOL
 * quote, in the program's positional order: the quote mint, the bonding
 * curve's quote ATA (the program creates it, non-idempotently), the quote
 * token program, and the `QuoteControl` PDA. The PDA is always appended: the
 * program reads it only for a mint `Global` does not whitelist (a missing
 * fourth account then fails with 6063 `UnsupportedQuoteMint`), never reads it
 * for a `Global` mint, and the program deployed before quote control ignores
 * a fourth account altogether.
 */
function createV2QuoteRemainingAccounts({
  mint,
  quoteMint,
  quoteTokenProgram,
  pumpQuote,
}: {
  mint: PublicKey;
  quoteMint: PublicKey;
  quoteTokenProgram: PublicKey;
  pumpQuote?: PumpQuoteAccounts;
}): AccountMeta[] {
  const readonly = (pubkey: PublicKey): AccountMeta => ({
    pubkey,
    isWritable: false,
    isSigner: false,
  });
  return [
    readonly(quoteMint),
    {
      pubkey: quoteAta(bondingCurvePda(mint), quoteMint, quoteTokenProgram),
      isWritable: true,
      isSigner: false,
    },
    readonly(quoteTokenProgram),
    readonly(QUOTE_CONTROL_PDA),
    ...(pumpQuote
      ? [
          { mint: quoteMint, pool: pumpQuote.pool },
          ...(pumpQuote.chain ?? []),
        ].flatMap(({ mint: coin, pool }) => [
          readonly(bondingCurvePda(coin)),
          ...(pool
            ? [
                readonly(pool.pool),
                readonly(pool.baseVault),
                readonly(pool.quoteVault),
              ]
            : []),
        ])
      : []),
  ];
}

/**
 * The extra `create_v2` accounts that admit a pump coin Q as the quote mint
 * (listed neither on `Global` nor in quote control): one group per coin on
 * Q's quote chain, Q first, down to the depth-0 root. A group is the coin's
 * bonding curve, followed once that curve has migrated by its canonical
 * pump-amm pool and the pool's two vaults. `OnlinePumpSdk.fetchPumpQuote`
 * resolves them.
 */
export interface PumpQuoteAccounts {
  /** Q's pool accounts, once Q has migrated. */
  pool?: { pool: PublicKey; baseVault: PublicKey; quoteVault: PublicKey };
  /**
   * The coins below Q, nearest first (`Q.depth` of them; empty for a depth-0
   * Q), each with its pool accounts once migrated.
   */
  chain?: {
    mint: PublicKey;
    pool?: { pool: PublicKey; baseVault: PublicKey; quoteVault: PublicKey };
  }[];
}

/**
 * The quote `buy_v2` must be built with after a `create_v2`
 * given the same inputs. The create ignores `quoteTokenProgram` on its SOL
 * branch (WSOL, the zero key, `undefined`), so the buy must too: SOL is always
 * `NATIVE_MINT` under SPL Token, whatever program the caller passed.
 */
function createAndBuyQuote(
  quoteMint: PublicKey | undefined,
  quoteTokenProgram: PublicKey,
): { buyQuoteMint: PublicKey; buyQuoteTokenProgram: PublicKey } {
  return quoteMint && !isLegacyQuoteMint(quoteMint)
    ? { buyQuoteMint: quoteMint, buyQuoteTokenProgram: quoteTokenProgram }
    : { buyQuoteMint: NATIVE_MINT, buyQuoteTokenProgram: TOKEN_PROGRAM_ID };
}

/**
 * A quote mint and the program that owns it, as needed to derive the
 * associated token accounts that hold that quote.
 */
export interface QuoteMintCandidate {
  mint: PublicKey;
  tokenProgram: PublicKey;
}

// The quote mints `getCoinCreatorVaultQuoteMint` recognizes by default: WSOL,
// mainnet USDC and devnet USDC, all SPL Token. Quote-control mints are not
// static, so callers that may meet one build the list from
// `OnlinePumpSdk.fetchSupportedQuoteMints` / `resolveQuoteMint` instead.
const DEFAULT_VAULT_QUOTE_CANDIDATES: readonly QuoteMintCandidate[] =
  Object.freeze([
    { mint: NATIVE_MINT, tokenProgram: TOKEN_PROGRAM_ID },
    {
      mint: new PublicKey("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"),
      tokenProgram: TOKEN_PROGRAM_ID,
    },
    {
      mint: new PublicKey("4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"),
      tokenProgram: TOKEN_PROGRAM_ID,
    },
  ]);

/**
 * The accounts `buy_v3`, `buy_exact_quote_in_v3` and `sell_v3` share, minus
 * the ones Anchor resolves by itself (`global`, `bonding_curve`,
 * `user_volume_accumulator`, `fee_config`, ...). `quoteMint` may be the
 * curve's stored quote (the zero key is SOL).
 *
 * `buyback_fee_recipient` receives the buyback slice in the trade: on a SOL
 * curve a listed `Global.buybackFeeRecipients` wallet itself (random by
 * default), on a token quote that wallet's canonical `quoteMint` ATA (the
 * first listed wallet by default). The program refuses anything else and
 * never creates the ATA.
 */
function tradeV3Accounts({
  user,
  mint,
  tokenProgram,
  quoteMint,
  quoteTokenProgram,
  buybackFeeRecipient,
}: {
  user: PublicKey;
  mint: PublicKey;
  tokenProgram: PublicKey;
  quoteMint: PublicKey;
  quoteTokenProgram: PublicKey;
  buybackFeeRecipient?: PublicKey;
}) {
  const quote = normalizeQuoteMint(quoteMint);
  const bondingCurve = bondingCurvePda(mint);
  return {
    baseMint: mint,
    quoteMint: quote,
    baseTokenProgram: tokenProgram,
    quoteTokenProgram,
    associatedBaseBondingCurve: getAssociatedTokenAddressSync(
      mint,
      bondingCurve,
      true,
      tokenProgram,
    ),
    associatedQuoteBondingCurve: quoteAta(
      bondingCurve,
      quote,
      quoteTokenProgram,
    ),
    user,
    associatedBaseUser: getAssociatedTokenAddressSync(
      mint,
      user,
      true,
      tokenProgram,
    ),
    associatedQuoteUser: quoteAta(user, quote, quoteTokenProgram),
    buybackFeeRecipient: isLegacyQuoteMint(quote)
      ? (buybackFeeRecipient ?? getStaticRandomFeeRecipientForBuyback())
      : quoteAta(
          buybackFeeRecipient ?? getBuybackFeeRecipientForTokenQuote(),
          quote,
          quoteTokenProgram,
        ),
  };
}

/**
 * An idempotent create of the buyback recipient's quote ATA a token-quoted v3
 * trade or route pays the slice into (the program refuses a missing one and
 * never creates it), paid by `payer`; a no-op when it exists. None for a v3
 * trade on a SOL curve, which pays the wallet itself; a route always pays an
 * ATA (WSOL for SOL), so `route` keeps it.
 */
function buybackAtaInstructions(
  payer: PublicKey,
  quoteMint: PublicKey,
  quoteTokenProgram: PublicKey,
  buybackFeeRecipient?: PublicKey,
  route = false,
): TransactionInstruction[] {
  const quote = normalizeQuoteMint(quoteMint);
  if (isLegacyQuoteMint(quote) && !route) {
    return [];
  }
  const recipient =
    buybackFeeRecipient ?? getBuybackFeeRecipientForTokenQuote();
  return [
    createAssociatedTokenAccountIdempotentInstruction(
      payer,
      quoteAta(recipient, quote, quoteTokenProgram),
      recipient,
      quote,
      quoteTokenProgram,
    ),
  ];
}

/**
 * The accounts `sweep_protocol_fee` and `sweep_creator_fee` share.
 * `quoteMint` may be the curve's stored quote (the zero key is SOL).
 */
function sweepBondingCurveFeeAccounts({
  payer,
  mint,
  recipient,
  quoteMint,
  quoteTokenProgram,
}: {
  payer: PublicKey;
  mint: PublicKey;
  recipient: PublicKey;
  quoteMint: PublicKey;
  quoteTokenProgram: PublicKey;
}) {
  const quote = normalizeQuoteMint(quoteMint);
  return {
    payer,
    baseMint: mint,
    quoteMint: quote,
    quoteTokenProgram,
    associatedQuoteBondingCurve: quoteAta(
      bondingCurvePda(mint),
      quote,
      quoteTokenProgram,
    ),
    recipient,
    associatedQuoteRecipient: quoteAta(recipient, quote, quoteTokenProgram),
    eventAuthority: PUMP_EVENT_AUTHORITY_PDA,
    program: PUMP_PROGRAM_ID,
  };
}

/**
 * One hop of a `multi_hop_swap` route: a coin (`baseMint`) traded against
 * its quote (`quoteMint`) on its canonical pump-amm pool or on its pump
 * bonding curve, SOL-quoted curves included. SOL is WSOL in a route (the
 * zero key a SOL curve stores is read as WSOL): such a curve hop sends
 * `NATIVE_MINT` as its quote mint and the curve's WSOL ATA as its quote
 * vault, the same 5-account layout as any other hop.
 */
export interface MultiHopHop {
  venue: "pool" | "curve";
  baseMint: PublicKey;
  quoteMint: PublicKey;
  baseTokenProgram: PublicKey;
  quoteTokenProgram: PublicKey;
}

/**
 * A route's direction: `buy` walks a quote chain up (each hop buys a coin
 * quoted in the previous hop's coin), `sell` walks it down. Every hop of a
 * route trades the same way (pump-amm 6086 `MultiHopMixedDirection`).
 */
export type MultiHopSide = "buy" | "sell";

// A hop with SOL as stored on curves (the zero key) read as WSOL under SPL
// Token, the only form routes and pools know.
function normalizeHop(hop: MultiHopHop): MultiHopHop {
  const side = (mint: PublicKey, tokenProgram: PublicKey) =>
    isLegacyQuoteMint(mint)
      ? { mint: NATIVE_MINT, tokenProgram: TOKEN_PROGRAM_ID }
      : { mint, tokenProgram };
  const base = side(hop.baseMint, hop.baseTokenProgram);
  const quote = side(hop.quoteMint, hop.quoteTokenProgram);
  return {
    venue: hop.venue,
    baseMint: base.mint,
    baseTokenProgram: base.tokenProgram,
    quoteMint: quote.mint,
    quoteTokenProgram: quote.tokenProgram,
  };
}

/**
 * The mints and token programs a route starts and ends in, checking that the
 * hops chain (pump-amm 6084 `MultiHopDiscontinuousPath` otherwise). SOL may
 * be given as WSOL or as the zero key curves store; it comes back as WSOL. The
 * protocol leg (first hop of a buy, last of a sell) trades the user's
 * currency: `input` on a buy, `output` on a sell.
 */
export function multiHopRouteEnds(
  rawHops: readonly MultiHopHop[],
  side: MultiHopSide,
): {
  input: { mint: PublicKey; tokenProgram: PublicKey };
  output: { mint: PublicKey; tokenProgram: PublicKey };
  currency: { mint: PublicKey; tokenProgram: PublicKey };
} {
  const hops = rawHops.map(normalizeHop);
  if (hops.length === 0) {
    throw new Error("multi_hop_swap: a route needs at least one hop");
  }
  const isBuy = side === "buy";
  for (const [index, hop] of hops.entries()) {
    const next = hops[index + 1];
    if (
      next &&
      !(isBuy ? next.quoteMint : next.baseMint).equals(
        isBuy ? hop.baseMint : hop.quoteMint,
      )
    ) {
      throw new Error(
        `multi_hop_swap: hop ${index + 1} does not continue from hop ${index}`,
      );
    }
  }
  const first = hops[0];
  const last = hops[hops.length - 1];
  const input = isBuy
    ? { mint: first.quoteMint, tokenProgram: first.quoteTokenProgram }
    : { mint: first.baseMint, tokenProgram: first.baseTokenProgram };
  const output = isBuy
    ? { mint: last.baseMint, tokenProgram: last.baseTokenProgram }
    : { mint: last.quoteMint, tokenProgram: last.quoteTokenProgram };
  return { input, output, currency: isBuy ? input : output };
}

// One hop's 5-account group: base mint, quote mint, venue, base vault, quote
// vault. Canonical pools and curves hold their vaults at their ATAs.
function multiHopHopAccounts(rawHop: MultiHopHop): AccountMeta[] {
  const hop = normalizeHop(rawHop);
  const venue =
    hop.venue === "pool"
      ? canonicalPumpPoolPdaWithQuote(hop.baseMint, hop.quoteMint)
      : bondingCurvePda(hop.baseMint);
  const writable = (pubkey: PublicKey): AccountMeta => ({
    pubkey,
    isWritable: true,
    isSigner: false,
  });
  return [
    { pubkey: hop.baseMint, isWritable: false, isSigner: false },
    { pubkey: hop.quoteMint, isWritable: false, isSigner: false },
    writable(venue),
    writable(quoteAta(venue, hop.baseMint, hop.baseTokenProgram)),
    writable(quoteAta(venue, hop.quoteMint, hop.quoteTokenProgram)),
  ];
}

export class PumpSdk {
  private readonly offlinePumpProgram: Program<Pump>;
  private readonly offlinePumpFeeProgram: Program<PumpFees>;
  private readonly offlinePumpAmmProgram: Program<PumpAmm>;

  constructor() {
    this.offlinePumpProgram = OFFLINE_PUMP_PROGRAM;
    // Create offline programs for fee and AMM
    this.offlinePumpFeeProgram = new Program(
      PumpFeesIdl as PumpFees,
      new AnchorProvider(null as any, null as any, {}),
    );
    this.offlinePumpAmmProgram = new Program(
      PumpAmmIdl as PumpAmm,
      new AnchorProvider(null as any, null as any, {}),
    );
  }

  /**
   * Decodes the pump `Global` account, including the live 1045-byte account
   * that predates `creatorFeeConfigurable` / `maxConfigurableCreatorFeeBps`
   * (they read `false` / 0, see `GLOBAL_SIZE`).
   */
  decodeGlobal(accountInfo: AccountInfo<Buffer>): Global {
    return this.offlinePumpProgram.coder.accounts.decode<Global>(
      "global",
      zeroPadded(accountInfo.data, GLOBAL_SIZE),
    );
  }

  /**
   * Decodes a pump-fees `FeeConfig` account the way the program does
   * (`FeeConfig::deserialize_versioned`): the account length selects the
   * layout version, and the bytes after that version's last field are never
   * read. `stableFeeTiers` is empty below `FEE_CONFIG_POST_STABLE_SIZE` and
   * `exoticFlatFees` is all-zero (unset) below `FEE_CONFIG_CURRENT_SIZE`,
   * whatever bytes follow the shorter layout (a pre-allocated tail, or stale
   * tier bytes left behind when a vector was upserted shorter). Throws on data
   * shorter than `FEE_CONFIG_INITIALIZE_SIZE` or a tier vector the program
   * could not have written.
   */
  decodeFeeConfig(accountInfo: AccountInfo<Buffer>): FeeConfig {
    const { data } = accountInfo;
    if (data.length < FEE_CONFIG_INITIALIZE_SIZE) {
      throw new Error(
        `Invalid FeeConfig account: ${data.length} bytes, expected at least ${FEE_CONFIG_INITIALIZE_SIZE}`,
      );
    }

    // Where the version the length selects stops reading.
    const feeTiersEnd = feeTierVecEnd(data, FEE_CONFIG_FEE_TIERS_OFFSET);
    let readEnd: number;
    if (data.length < FEE_CONFIG_POST_STABLE_SIZE) {
      readEnd = feeTiersEnd;
    } else {
      const stableFeeTiersEnd = feeTierVecEnd(data, feeTiersEnd);
      readEnd =
        data.length < FEE_CONFIG_CURRENT_SIZE
          ? stableFeeTiersEnd
          : stableFeeTiersEnd + FEES_LEN;
    }

    // Hand the coder exactly the bytes the program reads, then zeros: a missing
    // `stable_fee_tiers` decodes as an empty vector and a missing
    // `exotic_flat_fees` as all-zero, which is also the program's default.
    return this.offlinePumpProgram.coder.accounts.decode<FeeConfig>(
      "feeConfig",
      Buffer.concat([
        data.subarray(0, readEnd),
        Buffer.alloc(VEC_LEN_PREFIX + FEES_LEN),
      ]),
    );
  }

  /**
   * Decodes a `BondingCurve` of every length the program has written (49, 81,
   * 82, 83, 115, 124, 125, 141, the extended 151 and the current 166 bytes)
   * the way its
   * versioned reader does: every layout is a prefix of the next and the
   * fields a shorter account lacks read as their defaults (the zero key,
   * `false`, zero). Bytes past `BONDING_CURVE_SIZE` (an extended curve) are
   * ignored. Throws below
   * the 49-byte initial layout, as the program does. A length the program
   * never writes (say 100 bytes) is not special-cased: the program would read
   * it as the longest layout that fits and ignore the rest, this zero-padded
   * read takes the extra bytes as the start of the next field.
   */
  decodeBondingCurve(accountInfo: AccountInfo<Buffer>): BondingCurve {
    const { data } = accountInfo;
    if (data.length < BONDING_CURVE_INITIALIZE_SIZE) {
      throw new Error(
        `Invalid BondingCurve account: ${data.length} bytes, expected at least ${BONDING_CURVE_INITIALIZE_SIZE}`,
      );
    }
    return this.offlinePumpProgram.coder.accounts.decode<BondingCurve>(
      "bondingCurve",
      zeroPadded(data, BONDING_CURVE_SIZE),
    );
  }

  /**
   * The quote mint a pump-amm coin creator vault ATA holds, found by matching
   * the ATA against `candidates`.
   *
   * @param candidates - The quote mints to try, each with the program that
   *   owns it (the ATA is derived with it). Defaults to WSOL, mainnet USDC and
   *   devnet USDC under SPL Token. Quote-control mints and Token-2022 quotes
   *   are only found when passed here; build the list from
   *   `OnlinePumpSdk.fetchSupportedQuoteMints` plus each mint's
   *   `fetchQuoteTokenProgram` (or `resolveQuoteMint`).
   * @returns The matching mint, or `null` when no candidate matches.
   */
  getCoinCreatorVaultQuoteMint(
    coinCreator: PublicKey,
    coinCreatorVaultAta: PublicKey,
    candidates: readonly QuoteMintCandidate[] = DEFAULT_VAULT_QUOTE_CANDIDATES,
  ): PublicKey | null {
    const vaultAuthority = ammCreatorVaultPda(coinCreator);

    for (const { mint, tokenProgram } of candidates) {
      const ata = getAssociatedTokenAddressSync(
        mint,
        vaultAuthority,
        true,
        tokenProgram,
      );
      if (ata.equals(coinCreatorVaultAta)) {
        return mint;
      }
    }

    return null;
  }

  decodeBondingCurveNullable(
    accountInfo: AccountInfo<Buffer>,
  ): BondingCurve | null {
    try {
      return this.decodeBondingCurve(accountInfo);
    } catch (error) {
      console.warn("Failed to decode bonding curve", error);
      return null;
    }
  }

  /**
   * Decodes the pump `QuoteControl` PDA. Like the program's raw reader
   * (`QuoteControl::lookup_initial_virtual_quote_reserves`, error 6075
   * `InvalidQuoteControl`), the declared `mints` length must fit in the data;
   * bytes past it (the pre-allocated tail, or stale entries left behind by a
   * remove) are ignored. The program never writes an over-declared account
   * (it grows before it pushes and never shrinks), so this only rejects
   * corrupt or foreign data, which would otherwise decode as phantom zero-key
   * entries or, for a huge count, allocate until the process dies.
   */
  decodeQuoteControl(accountInfo: AccountInfo<Buffer>): QuoteControl {
    const { data } = accountInfo;
    if (data.length < QUOTE_CONTROL_HEADER_LEN) {
      throw new Error(
        `Invalid QuoteControl account: ${data.length} bytes, expected at least ${QUOTE_CONTROL_HEADER_LEN}`,
      );
    }
    const count = data.readUInt32LE(QUOTE_CONTROL_LEN_OFFSET);
    if (
      QUOTE_CONTROL_HEADER_LEN + count * QUOTE_CONTROL_ENTRY_LEN >
      data.length
    ) {
      throw new Error(
        `Invalid QuoteControl account: ${count} entries declared in ${data.length} bytes`,
      );
    }

    return this.offlinePumpProgram.coder.accounts.decode<QuoteControl>(
      "quoteControl",
      data,
    );
  }

  /**
   * `null` when the account is missing (the PDA is not initialized yet, which
   * the program treats as an empty list) or does not decode as a
   * `QuoteControl` (wrong discriminator, over-declared length; logged with
   * `console.warn`). Note that `OnlinePumpSdk.fetchQuoteControl` is stricter:
   * it returns `null` only for a missing account and throws on a malformed
   * one.
   */
  decodeQuoteControlNullable(
    accountInfo: AccountInfo<Buffer> | null,
  ): QuoteControl | null {
    if (!accountInfo) {
      return null;
    }

    try {
      return this.decodeQuoteControl(accountInfo);
    } catch (error) {
      console.warn("Failed to decode quote control", error);
      return null;
    }
  }

  decodeGlobalVolumeAccumulator(
    accountInfo: AccountInfo<Buffer>,
  ): GlobalVolumeAccumulator {
    return this.offlinePumpProgram.coder.accounts.decode<GlobalVolumeAccumulator>(
      "globalVolumeAccumulator",
      accountInfo.data,
    );
  }

  decodeUserVolumeAccumulator(
    accountInfo: AccountInfo<Buffer>,
  ): UserVolumeAccumulator {
    return this.offlinePumpProgram.coder.accounts.decode<UserVolumeAccumulator>(
      "userVolumeAccumulator",
      accountInfo.data,
    );
  }

  decodeUserVolumeAccumulatorNullable(
    accountInfo: AccountInfo<Buffer>,
  ): UserVolumeAccumulator | null {
    try {
      return this.decodeUserVolumeAccumulator(accountInfo);
    } catch (error) {
      console.warn("Failed to decode user volume accumulator", error);
      return null;
    }
  }

  decodeSharingConfig(accountInfo: AccountInfo<Buffer>): SharingConfig {
    return this.offlinePumpFeeProgram.coder.accounts.decode<SharingConfig>(
      "sharingConfig",
      accountInfo.data,
    );
  }

  decodeSocialFeePda(accountInfo: AccountInfo<Buffer>): SocialFeePdaState {
    return this.offlinePumpFeeProgram.coder.accounts.decode<SocialFeePdaState>(
      "socialFeePda",
      accountInfo.data,
    );
  }

  decodeSocialFeePdaClaimedEvent(data: Buffer): SocialFeePdaClaimedEvent {
    return this.offlinePumpFeeProgram.coder.types.decode<SocialFeePdaClaimedEvent>(
      "socialFeePdaClaimed",
      data,
    );
  }

  decodeSocialFeePdaCreatedEvent(data: Buffer): SocialFeePdaCreatedEvent {
    return this.offlinePumpFeeProgram.coder.types.decode<SocialFeePdaCreatedEvent>(
      "socialFeePdaCreated",
      data,
    );
  }

  decodeCreateFeeSharingConfigEvent(data: Buffer): CreateFeeSharingConfigEvent {
    return this.offlinePumpFeeProgram.coder.types.decode<CreateFeeSharingConfigEvent>(
      "createFeeSharingConfigEvent",
      data,
    );
  }

  decodeUpdateFeeSharesEvent(data: Buffer): UpdateFeeSharesEvent {
    return this.offlinePumpFeeProgram.coder.types.decode<UpdateFeeSharesEvent>(
      "updateFeeSharesEvent",
      data,
    );
  }

  decodeUpdateAdminEvent(data: Buffer): UpdateAdminEvent {
    return this.offlinePumpFeeProgram.coder.types.decode<UpdateAdminEvent>(
      "updateAdminEvent",
      data,
    );
  }

  decodeSetAuthorityEvent(data: Buffer): SetAuthorityEvent {
    return this.offlinePumpFeeProgram.coder.types.decode<SetAuthorityEvent>(
      "setAuthorityEvent",
      data,
    );
  }

  decodeResetFeeSharingConfigEvent(data: Buffer): ResetFeeSharingConfigEvent {
    return this.offlinePumpFeeProgram.coder.types.decode<ResetFeeSharingConfigEvent>(
      "resetFeeSharingConfigEvent",
      data,
    );
  }

  decodeDonationFeePdaCreatedEvent(data: Buffer): DonationFeePdaCreatedEvent {
    return this.offlinePumpFeeProgram.coder.types.decode<DonationFeePdaCreatedEvent>(
      "donationFeePdaCreated",
      data,
    );
  }

  decodeCollectCreatorFeeEventBc(data: Buffer): CollectCreatorFeeEventBc {
    return this.offlinePumpProgram.coder.types.decode<CollectCreatorFeeEventBc>(
      "collectCreatorFeeEvent",
      data,
    );
  }

  decodeCollectCoinCreatorFeeEventAmm(
    data: Buffer,
  ): CollectCoinCreatorFeeEventAmm {
    return this.offlinePumpAmmProgram.coder.types.decode<CollectCoinCreatorFeeEventAmm>(
      "collectCoinCreatorFeeEvent",
      data,
    );
  }

  /**
   * Decodes a pump-amm `CreatePoolEvent` emitted under any layout. The
   * vendored IDL ends the event with `creator_fee_bps: u64`,
   * `can_edit_creator_fee: bool` (configurable creator fees) and
   * `is_holder_reward: bool` (holder-reward coins); the program deployed
   * before the last emits it one byte shorter, the one before the other two
   * ten bytes shorter. The borsh coder rejects either with a RangeError, so
   * the event is retried with the missing fields' defaults appended
   * (`creatorFeeBps` zero, `canEditCreatorFee` / `isHolderReward` false). An
   * event shorter than the oldest layout still throws.
   */
  decodeCreatePoolEventAmm(data: Buffer): CreatePoolEventAmm {
    return decodeWithTrailingDefaults(
      data,
      CREATE_POOL_EVENT_LAYOUT_PADDINGS,
      (bytes) =>
        this.offlinePumpAmmProgram.coder.types.decode<CreatePoolEventAmm>(
          "createPoolEvent",
          bytes,
        ),
    );
  }

  decodeDepositEventAmm(data: Buffer): DepositEventAmm {
    return decodeWithTrailingDefaults(
      data,
      LIQUIDITY_EVENT_LAYOUT_PADDINGS,
      (bytes) =>
        this.offlinePumpAmmProgram.coder.types.decode<DepositEventAmm>(
          "depositEvent",
          bytes,
        ),
    );
  }

  decodeWithdrawEventAmm(data: Buffer): WithdrawEventAmm {
    return decodeWithTrailingDefaults(
      data,
      LIQUIDITY_EVENT_LAYOUT_PADDINGS,
      (bytes) =>
        this.offlinePumpAmmProgram.coder.types.decode<WithdrawEventAmm>(
          "withdrawEvent",
          bytes,
        ),
    );
  }

  /**
   * Decodes a pump-amm `BuyEvent` emitted under any deployment's layout: the
   * vendored IDL ends it with `holder_rewards_bps` / `holder_rewards`
   * (holder-reward coins) then `creator_fee_unclaimed` (the pool's creator
   * bucket after the trade); an event from a program without them decodes
   * with the missing fields zero.
   */
  decodeBuyEventAmm(data: Buffer): BuyEventAmm {
    return decodeWithTrailingDefaults(
      data,
      TRADE_EVENT_LAYOUT_PADDINGS,
      (bytes) =>
        this.offlinePumpAmmProgram.coder.types.decode<BuyEventAmm>(
          "buyEvent",
          bytes,
        ),
    );
  }

  /** Like `decodeBuyEventAmm`, for `SellEvent`. */
  decodeSellEventAmm(data: Buffer): SellEventAmm {
    return decodeWithTrailingDefaults(
      data,
      TRADE_EVENT_LAYOUT_PADDINGS,
      (bytes) =>
        this.offlinePumpAmmProgram.coder.types.decode<SellEventAmm>(
          "sellEvent",
          bytes,
        ),
    );
  }

  decodeAdminCtoPoolEventAmm(data: Buffer): AdminCtoPoolEventAmm {
    return this.offlinePumpAmmProgram.coder.types.decode<AdminCtoPoolEventAmm>(
      "adminCtoPoolEvent",
      data,
    );
  }

  /**
   * Decodes a bonding-curve `CreateEvent` emitted under any deployment's
   * layout. The vendored IDL ends the event with `creator_fee_bps: u64`
   * (configurable creator fees), `is_holder_reward: bool` (holder-reward
   * coins) then `depth: u8` (pump-coin quotes). A program without some of
   * these trailing fields emits a shorter event; the borsh coder rejects it
   * with a RangeError, so the event is retried with the missing fields'
   * encodings appended, shortest padding first. A missing field decodes as
   * its default: `creatorFeeBps` zero, `isHolderReward` false, `depth` 0. An
   * event truncated inside a field still throws.
   */
  decodeCreateEventBc(data: Buffer): CreateEventBc {
    return decodeWithTrailingDefaults(
      data,
      CREATE_EVENT_LAYOUT_PADDINGS,
      (bytes) =>
        this.offlinePumpProgram.coder.types.decode<CreateEventBc>(
          "createEvent",
          bytes,
        ),
    );
  }

  /**
   * Decodes a bonding-curve `TradeEvent` emitted under any deployment's
   * layout: the vendored IDL ends it with `holder_rewards_bps` /
   * `holder_rewards` (holder-reward coins) then `creator_fee_unclaimed` (the
   * curve's creator bucket after the trade); an event from a program without
   * them decodes with the missing fields zero.
   */
  decodeTradeEventBc(data: Buffer): TradeEventBc {
    return decodeWithTrailingDefaults(
      data,
      TRADE_EVENT_LAYOUT_PADDINGS,
      (bytes) =>
        this.offlinePumpProgram.coder.types.decode<TradeEventBc>(
          "tradeEvent",
          bytes,
        ),
    );
  }

  decodeCompleteEventBc(data: Buffer): CompleteEventBc {
    return this.offlinePumpProgram.coder.types.decode<CompleteEventBc>(
      "completeEvent",
      data,
    );
  }

  decodeAdminCtoEvent(data: Buffer): AdminCtoEvent {
    return this.offlinePumpProgram.coder.types.decode<AdminCtoEvent>(
      "adminCtoEvent",
      data,
    );
  }

  decodeDistributeFeeToHoldersEvent(data: Buffer): DistributeFeeToHoldersEvent {
    return this.offlinePumpProgram.coder.types.decode<DistributeFeeToHoldersEvent>(
      "distributeFeeToHoldersEvent",
      data,
    );
  }

  decodeSetQuoteControlAdminEvent(data: Buffer): SetQuoteControlAdminEvent {
    return this.offlinePumpProgram.coder.types.decode<SetQuoteControlAdminEvent>(
      "setQuoteControlAdminEvent",
      data,
    );
  }

  decodeAddQuoteControlMintEvent(data: Buffer): AddQuoteControlMintEvent {
    return this.offlinePumpProgram.coder.types.decode<AddQuoteControlMintEvent>(
      "addQuoteControlMintEvent",
      data,
    );
  }

  decodeRemoveQuoteControlMintEvent(data: Buffer): RemoveQuoteControlMintEvent {
    return this.offlinePumpProgram.coder.types.decode<RemoveQuoteControlMintEvent>(
      "removeQuoteControlMintEvent",
      data,
    );
  }

  decodeUpdateCreatorFeeConfigEvent(data: Buffer): UpdateCreatorFeeConfigEvent {
    return this.offlinePumpProgram.coder.types.decode<UpdateCreatorFeeConfigEvent>(
      "updateCreatorFeeConfigEvent",
      data,
    );
  }

  decodeClaimCashbackEventBc(data: Buffer): ClaimCashbackEvent {
    return this.offlinePumpProgram.coder.types.decode<ClaimCashbackEvent>(
      "claimCashbackEvent",
      data,
    );
  }

  decodeClaimCashbackEventAmm(data: Buffer): ClaimCashbackEvent {
    return this.offlinePumpAmmProgram.coder.types.decode<ClaimCashbackEvent>(
      "claimCashbackEvent",
      data,
    );
  }

  decodePostCompleteBuyEvent(data: Buffer): PostCompleteBuyEvent {
    return this.offlinePumpProgram.coder.types.decode<PostCompleteBuyEvent>(
      "postCompleteBuyEvent",
      data,
    );
  }

  decodeSweepBondingCurveFeeEvent(data: Buffer): SweepBondingCurveFeeEvent {
    return this.offlinePumpProgram.coder.types.decode<SweepBondingCurveFeeEvent>(
      "sweepBondingCurveFeeEvent",
      data,
    );
  }

  decodeSweepPoolFeeEventAmm(data: Buffer): SweepPoolFeeEventAmm {
    return this.offlinePumpAmmProgram.coder.types.decode<SweepPoolFeeEventAmm>(
      "sweepPoolFeeEvent",
      data,
    );
  }

  decodeDonationFeePda(accountInfo: AccountInfo<Buffer>): DonationFeePdaState {
    return this.offlinePumpFeeProgram.coder.accounts.decode<DonationFeePdaState>(
      "donationFeePda",
      accountInfo.data,
    );
  }

  /**
   * @deprecated Use `createV2Instruction` instead.
   */
  async createInstruction({
    mint,
    name,
    symbol,
    uri,
    creator,
    user,
  }: {
    mint: PublicKey;
    name: string;
    symbol: string;
    uri: string;
    creator: PublicKey;
    user: PublicKey;
  }): Promise<TransactionInstruction> {
    return await this.offlinePumpProgram.methods
      .create(name, symbol, uri, creator)
      .accountsPartial({
        mint,
        user,
        tokenProgram: TOKEN_PROGRAM_ID,
      })
      .instruction();
  }

  /**
   * Builds `create_v2`. Without `quoteMint` (or with legacy WSOL / the zero
   * key) the curve is quoted in SOL and the instruction is unchanged from
   * earlier SDK versions. Any other `quoteMint` must be whitelisted on
   * `Global` or listed in the `QuoteControl` PDA
   * (`OnlinePumpSdk.fetchSupportedQuoteMints`) and is selected by four
   * positional remaining accounts: [0] the quote mint (read-only), [1] the
   * bonding curve's quote ATA derived under `quoteTokenProgram` (writable; the
   * program creates it), [2] `quoteTokenProgram` (read-only), [3] the
   * `QuoteControl` PDA (`QUOTE_CONTROL_PDA`, read-only). The PDA is always
   * sent: the program reads it only for a mint `Global` does not whitelist,
   * and the program deployed before quote control ignores a fourth account.
   *
   * A mint admitted only through quote control cannot be combined with
   * `mayhemMode` (6071 `MayhemModeQuoteMintNotAllowed`). Token-quoted creates
   * are heavy (a mayhem create with a token quote ~200-240k CU, the first
   * `buy_v2` on a Token-2022 quote ~200-220k), so add an explicit
   * `ComputeBudgetProgram.setComputeUnitLimit`: ~500k for create + buy with a
   * token quote, ~250-300k for a standalone `buy_v2` / `sell_v2` on a
   * Token-2022 quote.
   *
   * @param params.quoteTokenProgram - The program that owns `quoteMint`
   *   (`TOKEN_PROGRAM_ID` or `TOKEN_2022_PROGRAM_ID`); the program rejects a
   *   mismatch with 6063 `UnsupportedQuoteMint`. Defaults to
   *   `TOKEN_PROGRAM_ID`, which is right for USDC; resolve it with
   *   `OnlinePumpSdk.fetchQuoteTokenProgram` for anything else. Ignored for
   *   SOL.
   * @param params.creatorFeeBps - The coin's own creator fee rate in basis
   *   points (see `BondingCurve.creatorFeeBps`). Omitted or zero means the
   *   pump-fees schedule rate. Always encoded as the 8-byte `creator_fee_bps`
   *   argument, zero when unset. A nonzero rate needs
   *   `Global.creatorFeeConfigurable` and
   *   `1..=Global.maxConfigurableCreatorFeeBps` (6077 / 6078), and only a
   *   quote admitted through `QuoteControl` stores it (on SOL or USDC it is
   *   ignored); this builder encodes what it is given and leaves the program
   *   to judge. Quote the first buy with the same rate
   *   (`getBuyTokenAmountFromSolAmount`'s `creatorFeeBps`). The rate changes
   *   afterwards only through a CTO (`adminCtoInstruction`).
   * @param params.holderReward - Creates a holder-reward coin: the program
   *   ignores `creator` and makes the coin's `holderRewardsPda(mint)` the
   *   creator, so every creator fee accrues to that PDA's vault and is paid
   *   out to holders through `distribute_fee_to_holders`. Permanent. Always
   *   encoded as the trailing 1-byte `is_holder_reward` argument, `false`
   *   when unset: the program deployed before holder-reward coins ignores
   *   trailing instruction bytes, the new one reads them. Needs
   *   `Global.isHolderRewardEnabled` (6084). The first buy's creator vault
   *   must then be the PDA's: the create-and-buy builders handle it.
   * @param params.cashback - Deprecated. `create_v2` rejects `true` with 6082
   *   `CashbackDeprecated`; existing cashback coins are unaffected. Still
   *   encoded as given so the instruction bytes stay predictable.
   * @param params.pumpQuote - Set when `quoteMint` is a pump coin listed
   *   nowhere: appends Q's bonding curve (and, once Q migrated, its pool
   *   accounts), then the same group for each coin below Q. Such a coin seeds
   *   its reserves from the live reserves of Q's whole quote chain, stores
   *   `depth = Q.depth + 1` (at most `Global.maxCurveDepth` and 5), cannot be
   *   mayhem mode and may set `creatorFeeBps`. Budget ~200k CU; a deep chain
   *   of migrated coins needs a v0 transaction with a lookup table.
   */
  async createV2Instruction({
    mint,
    name,
    symbol,
    uri,
    creator,
    user,
    mayhemMode,
    cashback = false,
    quoteMint,
    quoteTokenProgram = TOKEN_PROGRAM_ID,
    creatorFeeBps,
    holderReward = false,
    pumpQuote,
  }: {
    mint: PublicKey;
    name: string;
    symbol: string;
    uri: string;
    creator: PublicKey;
    user: PublicKey;
    mayhemMode: boolean;
    /** @deprecated cashback coins can no longer be created (6082). */
    cashback?: boolean;
    quoteMint?: PublicKey;
    quoteTokenProgram?: PublicKey;
    creatorFeeBps?: BN;
    holderReward?: boolean;
    pumpQuote?: PumpQuoteAccounts;
  }): Promise<TransactionInstruction> {
    const builder = this.offlinePumpProgram.methods
      .createV2(
        name,
        symbol,
        uri,
        creator,
        mayhemMode,
        [cashback ?? false],
        [new BN(creatorFeeBps ?? 0)],
        [holderReward ?? false],
      )
      .accountsPartial({
        mint,
        user,
        tokenProgram: TOKEN_2022_PROGRAM_ID,
        mayhemProgramId: MAYHEM_PROGRAM_ID,
        globalParams: getGlobalParamsPda(),
        solVault: getSolVaultPda(),
        mayhemState: getMayhemStatePda(mint),
        mayhemTokenVault: getTokenVaultPda(mint),
      });

    if (quoteMint && !isLegacyQuoteMint(quoteMint)) {
      return await builder
        .remainingAccounts(
          createV2QuoteRemainingAccounts({
            mint,
            quoteMint,
            quoteTokenProgram,
            pumpQuote,
          }),
        )
        .instruction();
    }

    return await builder.instruction();
  }

  /**
   * `set_max_curve_depth`: how deep a pump-coin quote chain `create_v2` may
   * build (`Global.maxCurveDepth`; 0 disables pump-coin quotes, 1 admits
   * coins quoted in depth-0 coins only; the program caps it at
   * `MAX_CURVE_DEPTH`, 5, whatever is set). `authority` signs and must be
   * `Global.authority`.
   */
  async setMaxCurveDepthInstruction({
    authority,
    maxCurveDepth,
  }: {
    authority: PublicKey;
    maxCurveDepth: number;
  }): Promise<TransactionInstruction> {
    return await this.offlinePumpProgram.methods
      .setMaxCurveDepth(maxCurveDepth)
      .accountsPartial({
        global: GLOBAL_PDA,
        authority,
        eventAuthority: PUMP_EVENT_AUTHORITY_PDA,
        program: PUMP_PROGRAM_ID,
      })
      .instruction();
  }

  async buyInstructions({
    global,
    bondingCurveAccountInfo,
    bondingCurve,
    associatedUserAccountInfo,
    mint,
    user,
    amount,
    solAmount,
    slippage,
    tokenProgram = TOKEN_PROGRAM_ID,
  }: {
    global: Global;
    bondingCurveAccountInfo: AccountInfo<Buffer>;
    bondingCurve: BondingCurve;
    associatedUserAccountInfo: AccountInfo<Buffer> | null;
    mint: PublicKey;
    user: PublicKey;
    amount: BN;
    solAmount: BN;
    slippage: number;
    tokenProgram: PublicKey;
  }): Promise<TransactionInstruction[]> {
    const instructions: TransactionInstruction[] = [];

    const associatedUser = getAssociatedTokenAddressSync(
      mint,
      user,
      true,
      tokenProgram,
    );

    if (!associatedUserAccountInfo) {
      instructions.push(
        createAssociatedTokenAccountIdempotentInstruction(
          user,
          associatedUser,
          user,
          mint,
          tokenProgram,
        ),
      );
    }

    instructions.push(
      await this.buyInstruction({
        global,
        mint,
        creator: bondingCurve.creator,
        user,
        associatedUser,
        amount,
        solAmount,
        slippage,
        tokenProgram,
        mayhemMode: bondingCurve.isMayhemMode,
      }),
    );

    return instructions;
  }

  /**
   * `create_v2` + the user's base ATA + a first legacy `buy`, SOL-quoted.
   *
   * @param params.creatorFeeBps - Forwarded to `createV2Instruction`. Unlike
   *   that builder this one holds `global`, so a nonzero rate the program
   *   would reject throws up front: `CreatorFeeNotConfigurableError` (gate
   *   off), `CreatorFeeBpsOutOfRangeError` (outside
   *   `1..=global.maxConfigurableCreatorFeeBps`). Quote `amount` with the same
   *   rate (`getBuyTokenAmountFromSolAmount`'s `creatorFeeBps`), or the buy's
   *   `solAmount` falls short of the fees the program charges.
   * @param params.holderReward - Forwarded to `createV2Instruction`; the buy
   *   then targets the holder-rewards PDA's creator vault, as the program
   *   does. Throws `HolderRewardDisabledError` while
   *   `global.isHolderRewardEnabled` is off.
   * @param params.cashback - Deprecated: throws `CashbackDeprecatedError`
   *   when `true`, as `create_v2` would fail with 6082.
   */
  async createV2AndBuyInstructions({
    global,
    mint,
    name,
    symbol,
    uri,
    creator,
    user,
    amount,
    solAmount,
    mayhemMode,
    cashback,
    isTokenizedAgent = false,
    buyBackBps = 0,
    creatorFeeBps,
    holderReward = false,
  }: {
    global: Global;
    mint: PublicKey;
    name: string;
    symbol: string;
    uri: string;
    creator: PublicKey;
    user: PublicKey;
    amount: BN;
    solAmount: BN;
    mayhemMode: boolean;
    /** @deprecated cashback coins can no longer be created (6082). */
    cashback?: boolean;
    isTokenizedAgent?: boolean;
    buyBackBps?: number;
    creatorFeeBps?: BN;
    holderReward?: boolean;
  }): Promise<TransactionInstruction[]> {
    assertCreateV2FlagsAllowed({
      global,
      mint,
      cashback,
      holderReward,
      creatorFeeBps,
    });
    const associatedUser = getAssociatedTokenAddressSync(
      mint,
      user,
      true,
      TOKEN_2022_PROGRAM_ID,
    );
    const buyInstruction = await this.buyInstruction({
      global,
      mint,
      creator: createdCurveCreator(mint, creator, holderReward),
      user,
      associatedUser,
      amount,
      solAmount,
      slippage: 1,
      tokenProgram: TOKEN_2022_PROGRAM_ID,
      mayhemMode,
    });

    const instructions = [
      await this.createV2Instruction({
        mint,
        name,
        symbol,
        uri,
        creator,
        user,
        mayhemMode,
        cashback,
        creatorFeeBps,
        holderReward,
      }),
      createAssociatedTokenAccountIdempotentInstruction(
        user,
        associatedUser,
        user,
        mint,
        TOKEN_2022_PROGRAM_ID,
      ),
      buyInstruction,
    ];

    if (isTokenizedAgent) {
      const agentPaymentsSdk = PumpAgentOffline.load(mint);
      const agentInitializeIx = await agentPaymentsSdk.create({
        authority: creator,
        mint,
        agentAuthority: creator,
        buybackBps: buyBackBps,
      });
      instructions.push(agentInitializeIx);
    }

    return instructions;
  }

  /**
   * @deprecated Use `createV2AndBuyInstructions` instead.
   */
  async createAndBuyInstructions({
    global,
    mint,
    name,
    symbol,
    uri,
    creator,
    user,
    amount,
    solAmount,
    isTokenizedAgent = false,
    buyBackBps = 0,
  }: {
    global: Global;
    mint: PublicKey;
    name: string;
    symbol: string;
    uri: string;
    creator: PublicKey;
    user: PublicKey;
    amount: BN;
    solAmount: BN;
    isTokenizedAgent?: boolean;
    buyBackBps?: number;
  }): Promise<TransactionInstruction[]> {
    const associatedUser = getAssociatedTokenAddressSync(mint, user, true);
    const buyInstruction = await this.buyInstruction({
      global,
      mint,
      creator,
      user,
      associatedUser,
      amount,
      solAmount,
      slippage: 1,
      tokenProgram: TOKEN_PROGRAM_ID,
      mayhemMode: false,
    });

    const instructions = [
      await this.createInstruction({ mint, name, symbol, uri, creator, user }),
      createAssociatedTokenAccountIdempotentInstruction(
        user,
        associatedUser,
        user,
        mint,
      ),
      buyInstruction,
    ];

    if (isTokenizedAgent) {
      const agentPaymentsSdk = PumpAgentOffline.load(mint);
      const agentInitializeIx = await agentPaymentsSdk.create({
        authority: creator,
        mint,
        agentAuthority: creator,
        buybackBps: buyBackBps,
      });
      instructions.push(agentInitializeIx);
    }

    return instructions;
  }

  private async buyInstruction({
    global,
    mint,
    creator,
    user,
    associatedUser,
    amount,
    solAmount,
    slippage,
    tokenProgram = TOKEN_PROGRAM_ID,
    mayhemMode = false,
  }: {
    global: Global;
    mint: PublicKey;
    creator: PublicKey;
    user: PublicKey;
    associatedUser: PublicKey;
    amount: BN;
    solAmount: BN;
    slippage: number;
    tokenProgram: PublicKey;
    mayhemMode: boolean;
  }) {
    return await this.getBuyInstructionInternal({
      user,
      associatedUser,
      mint,
      creator,
      feeRecipient: getFeeRecipient(global, mayhemMode),
      buybackFeeRecipient: getStaticRandomFeeRecipientForBuyback(),
      amount,
      solAmount: solAmount.add(
        solAmount.mul(new BN(Math.floor(slippage * 10))).div(new BN(1000)),
      ),
      tokenProgram,
    });
  }

  async sellInstructions({
    global,
    bondingCurveAccountInfo,
    bondingCurve,
    mint,
    user,
    amount,
    solAmount,
    slippage,
    tokenProgram = TOKEN_PROGRAM_ID,
    mayhemMode = false,
    cashback = false,
  }: {
    global: Global;
    bondingCurveAccountInfo: AccountInfo<Buffer>;
    bondingCurve: BondingCurve;
    mint: PublicKey;
    user: PublicKey;
    amount: BN;
    solAmount: BN;
    slippage: number;
    tokenProgram: PublicKey;
    mayhemMode: boolean;
    cashback?: boolean;
  }): Promise<TransactionInstruction[]> {
    const instructions: TransactionInstruction[] = [];

    instructions.push(
      await this.getSellInstructionInternal({
        user,
        mint,
        creator: bondingCurve.creator,
        feeRecipient: getFeeRecipient(global, mayhemMode),
        buybackFeeRecipient: getStaticRandomFeeRecipientForBuyback(),
        amount,
        solAmount: solAmount.sub(
          solAmount.mul(new BN(Math.floor(slippage * 10))).div(new BN(1000)),
        ),
        tokenProgram,
        cashback,
      }),
    );

    return instructions;
  }

  async extendAccountInstruction({
    account,
    user,
  }: {
    account: PublicKey;
    user: PublicKey;
  }): Promise<TransactionInstruction> {
    return this.offlinePumpProgram.methods
      .extendAccount()
      .accountsPartial({
        account,
        user,
      })
      .instruction();
  }

  async migrateInstruction({
    withdrawAuthority,
    mint,
    user,
    tokenProgram = TOKEN_PROGRAM_ID,
  }: {
    withdrawAuthority: PublicKey;
    mint: PublicKey;
    user: PublicKey;
    tokenProgram: PublicKey;
  }): Promise<TransactionInstruction> {
    const bondingCurve = bondingCurvePda(mint);
    const associatedBondingCurve = getAssociatedTokenAddressSync(
      mint,
      bondingCurve,
      true,
      tokenProgram,
    );

    const poolAuthority = pumpPoolAuthorityPda(mint);
    const poolAuthorityMintAccount = getAssociatedTokenAddressSync(
      mint,
      poolAuthority,
      true,
      tokenProgram,
    );

    const pool = canonicalPumpPoolPda(mint);
    const poolBaseTokenAccount = getAssociatedTokenAddressSync(
      mint,
      pool,
      true,
      tokenProgram,
    );

    const boostVaultAuthority = boostVaultAuthorityPda(pool);
    const boostVault = getAssociatedTokenAddressSync(
      NATIVE_MINT,
      boostVaultAuthority,
      true,
      TOKEN_PROGRAM_ID,
    );
    const instruction = await this.offlinePumpProgram.methods
      .migrate()
      .accountsPartial({
        mint,
        user,
        withdrawAuthority,
        associatedBondingCurve,
        poolAuthorityMintAccount,
        poolBaseTokenAccount,
      })
      .remainingAccounts([
        { pubkey: boostVaultAuthority, isWritable: false, isSigner: false },
        { pubkey: boostVault, isWritable: true, isSigner: false },
      ])
      .instruction();
    assertBoostRemainingAccounts(
      instruction,
      MIGRATE_FIXED_ACCOUNTS,
      boostVaultAuthority,
      boostVault,
    );
    return instruction;
  }

  /**
   * @param params.quoteMint - The curve's quote mint; `bondingCurve.quoteMint`
   *   can be passed as is. `migrate_v2` accepts the mint the curve stores or,
   *   for a SOL curve (which stores the zero key), legacy WSOL, and the pool
   *   and every quote ATA are derived from WSOL in that case, so the zero key
   *   and `undefined` are normalized to `NATIVE_MINT`.
   * @param params.quoteTokenProgram - The program that owns `quoteMint`; all
   *   quote-side ATAs are derived with it. Defaults to `TOKEN_PROGRAM_ID`
   *   (SOL, USDC); pass `TOKEN_2022_PROGRAM_ID` for a Token-2022 quote.
   */
  async migrateV2Instruction({
    withdrawAuthority,
    mint,
    user,
    quoteMint: quoteMintOrDefault,
    baseTokenProgram = TOKEN_2022_PROGRAM_ID,
    quoteTokenProgram = TOKEN_PROGRAM_ID,
  }: {
    withdrawAuthority: PublicKey;
    mint: PublicKey;
    user: PublicKey;
    quoteMint?: PublicKey;
    baseTokenProgram: PublicKey;
    quoteTokenProgram: PublicKey;
  }): Promise<TransactionInstruction> {
    const quoteMint = normalizeQuoteMint(quoteMintOrDefault);
    const bondingCurve = bondingCurvePda(mint);

    const poolAuthority = pumpPoolAuthorityPda(mint);
    const poolAuthorityMintAccount = getAssociatedTokenAddressSync(
      mint,
      poolAuthority,
      true,
      baseTokenProgram,
    );

    const pool = canonicalPumpPoolPdaWithQuote(mint, quoteMint);
    const poolBaseTokenAccount = getAssociatedTokenAddressSync(
      mint,
      pool,
      true,
      baseTokenProgram,
    );

    const associatedBaseBondingCurve = getAssociatedTokenAddressSync(
      mint,
      bondingCurve,
      true,
      baseTokenProgram,
    );
    const associatedQuoteBondingCurve = quoteAta(
      bondingCurve,
      quoteMint,
      quoteTokenProgram,
    );
    const poolAuthorityQuoteAccount = quoteAta(
      poolAuthority,
      quoteMint,
      quoteTokenProgram,
    );
    const poolQuoteTokenAccount = getAssociatedTokenAddressSync(
      quoteMint,
      pool,
      true,
      quoteTokenProgram,
    );

    const boostVaultAuthority = boostVaultAuthorityPda(pool);
    const boostVault = getAssociatedTokenAddressSync(
      quoteMint,
      boostVaultAuthority,
      true,
      quoteTokenProgram,
    );
    const instruction = await this.offlinePumpProgram.methods
      .migrateV2()
      .accountsPartial({
        baseMint: mint,
        quoteMint,
        user,
        withdrawAuthority,
        bondingCurve,
        poolAuthorityMintAccount,
        poolBaseTokenAccount,
        pool,
        poolAuthority,
        systemProgram: SystemProgram.programId,
        pumpAmm: PUMP_AMM_PROGRAM_ID,
        pumpAmmEventAuthority: getEventAuthorityPda(PUMP_AMM_PROGRAM_ID),
        eventAuthority: getEventAuthorityPda(PUMP_PROGRAM_ID),
        program: PUMP_PROGRAM_ID,
        associatedBaseBondingCurve,
        associatedQuoteBondingCurve,
        poolAuthorityQuoteAccount,
        poolQuoteTokenAccount,
        baseTokenProgram,
        quoteTokenProgram,
      })
      .remainingAccounts([
        { pubkey: boostVaultAuthority, isWritable: false, isSigner: false },
        { pubkey: boostVault, isWritable: true, isSigner: false },
      ])
      .instruction();
    assertBoostRemainingAccounts(
      instruction,
      MIGRATE_V2_FIXED_ACCOUNTS,
      boostVaultAuthority,
      boostVault,
    );
    // A quote with a Token-2022 transfer fee has its withheld fees harvested
    // to the mint before the pool authority's quote account is closed, which
    // needs the mint writable (6110 `QuoteMintNotWritable` otherwise; the IDL
    // leaves it read-only so older transactions keep working). Harmless for
    // SOL and an untaxed quote.
    instruction.keys[MIGRATE_V2_QUOTE_MINT_INDEX].isWritable = true;
    return instruction;
  }

  async syncUserVolumeAccumulator(
    user: PublicKey,
  ): Promise<TransactionInstruction> {
    return await this.offlinePumpProgram.methods
      .syncUserVolumeAccumulator()
      .accountsPartial({ user })
      .instruction();
  }

  async setCreator({
    mint,
    setCreatorAuthority,
    creator,
  }: {
    mint: PublicKey;
    setCreatorAuthority: PublicKey;
    creator: PublicKey;
  }): Promise<TransactionInstruction> {
    return await this.offlinePumpProgram.methods
      .setCreator(creator)
      .accountsPartial({
        mint,
        setCreatorAuthority,
      })
      .instruction();
  }

  async initUserVolumeAccumulator({
    payer,
    user,
  }: {
    payer: PublicKey;
    user: PublicKey;
  }): Promise<TransactionInstruction> {
    return await this.offlinePumpProgram.methods
      .initUserVolumeAccumulator()
      .accountsPartial({ payer, user })
      .instruction();
  }

  async closeUserVolumeAccumulator(
    user: PublicKey,
  ): Promise<TransactionInstruction> {
    return await this.offlinePumpProgram.methods
      .closeUserVolumeAccumulator()
      .accountsPartial({ user })
      .instruction();
  }

  /**
   * `initialize_quote_control`: creates the `QuoteControl` PDA
   * (`QUOTE_CONTROL_PDA`) with no admin and an empty mint list. Permissionless
   * and once only (a second call fails in the system program, so nobody can
   * reset the list); `user` signs and pays the rent for the initial 2108
   * bytes. Only `Global.authority` can then assign an admin via
   * `setQuoteControlAdminInstruction`.
   */
  async initializeQuoteControlInstruction({
    user,
  }: {
    user: PublicKey;
  }): Promise<TransactionInstruction> {
    return await this.offlinePumpProgram.methods
      .initializeQuoteControl()
      .accountsPartial({ user })
      .instruction();
  }

  /**
   * `set_quote_control_admin`: `authority` must sign and be `Global.authority`.
   * The zero key revokes the admin, after which only `Global.authority` can
   * change the list.
   */
  async setQuoteControlAdminInstruction({
    authority,
    newAdmin,
  }: {
    authority: PublicKey;
    newAdmin: PublicKey;
  }): Promise<TransactionInstruction> {
    return await this.offlinePumpProgram.methods
      .setQuoteControlAdmin(newAdmin)
      .accountsPartial({ authority })
      .instruction();
  }

  /**
   * `add_quote_control_mint`: lists `quoteMint` as a `create_v2` quote, with
   * the `virtualQuoteReserves` a new curve quoted in it starts from (stored as
   * given, in the mint's base units). `authority` signs and must be
   * `QuoteControl.admin` or `Global.authority`; it pays the rent top-up when
   * the list grows past the 50 pre-allocated entries. The program rejects the
   * zero key, WSOL and the Token-2022 native mint (6069), a mint already
   * listed (6067; change its reserves with remove + add) and a full list of
   * 256 (6066). A mint `Global` whitelists may be listed too but keeps
   * `Global.initialVirtualQuoteReserves`.
   */
  async addQuoteControlMintInstruction({
    authority,
    quoteMint,
    initialVirtualQuoteReserves,
  }: {
    authority: PublicKey;
    quoteMint: PublicKey;
    initialVirtualQuoteReserves: BN;
  }): Promise<TransactionInstruction> {
    return await this.offlinePumpProgram.methods
      .addQuoteControlMint(quoteMint, initialVirtualQuoteReserves)
      .accountsPartial({ authority })
      .instruction();
  }

  /**
   * `remove_quote_control_mint`: de-lists `quoteMint` (6068 when it is not
   * listed). Same signer rule as `addQuoteControlMintInstruction`. Existing
   * curves quoted in the mint keep trading; only new `create_v2` calls are
   * refused.
   */
  async removeQuoteControlMintInstruction({
    authority,
    quoteMint,
  }: {
    authority: PublicKey;
    quoteMint: PublicKey;
  }): Promise<TransactionInstruction> {
    return await this.offlinePumpProgram.methods
      .removeQuoteControlMint(quoteMint)
      .accountsPartial({ authority })
      .instruction();
  }

  /**
   * `update_creator_fee_config`: turns per-coin creator fees on or off and
   * sets the ceiling a coin may configure (`Global.creatorFeeConfigurable`,
   * `Global.maxConfigurableCreatorFeeBps`). `authority` signs and must be
   * `Global.authority`. The program puts no bound on the ceiling: a rate that
   * pushes protocol + creator fees past 100% makes a coin buy-only. With the
   * gate off, configured rates are neither read nor accepted (kill switch).
   * Fails on the live 1045-byte `Global` until `extend_account` grows it to
   * `GLOBAL_SIZE`.
   */
  async updateCreatorFeeConfigInstruction({
    authority,
    creatorFeeConfigurable,
    maxConfigurableCreatorFeeBps,
  }: {
    authority: PublicKey;
    creatorFeeConfigurable: boolean;
    maxConfigurableCreatorFeeBps: BN;
  }): Promise<TransactionInstruction> {
    return await this.offlinePumpProgram.methods
      .updateCreatorFeeConfig(
        creatorFeeConfigurable,
        maxConfigurableCreatorFeeBps,
      )
      .accountsPartial({ authority })
      .instruction();
  }

  /**
   * `update_holder_reward_config`: turns holder-reward coin creation (and CTO
   * holder conversion) on or off and names the one signer
   * `distribute_fee_to_holders` accepts (`Global.isHolderRewardEnabled`,
   * `Global.holderRewardClaimAuthority`). `authority` signs and must be
   * `Global.authority`. Fails on a `Global` shorter than `GLOBAL_SIZE` until
   * `extend_account` grows it.
   */
  async updateHolderRewardConfigInstruction({
    authority,
    isHolderRewardEnabled,
    holderRewardClaimAuthority,
  }: {
    authority: PublicKey;
    isHolderRewardEnabled: boolean;
    holderRewardClaimAuthority: PublicKey;
  }): Promise<TransactionInstruction> {
    return await this.offlinePumpProgram.methods
      .updateHolderRewardConfig(
        isHolderRewardEnabled,
        holderRewardClaimAuthority,
      )
      .accountsPartial({ authority })
      .instruction();
  }

  /**
   * `admin_cto`, the one community-takeover instruction: re-points where a
   * coin's creator fees go on the bonding curve, its canonical pump-amm pool
   * (through `admin_cto_pool`, when one exists) and its pump-fees
   * `SharingConfig` (through `admin_cto_sharing_config`, when the coin is
   * fee-shared), in one transaction. `adminSetCreatorAuthority` signs, must
   * be `Global.adminSetCreatorAuthority`, and pays the rent that grows a
   * pre-upgrade curve or pool and any ATA created. Budget
   * `ADMIN_CTO_COMPUTE_UNIT_LIMIT` compute units.
   *
   * Two paths, chosen by the arguments (the program rejects the rest):
   * - **new creator**: `newCreator` set, `isHolderReward` unset or `false`.
   *   The outgoing wallet creator is first paid from both vaults; a
   *   fee-shared coin keeps its SharingConfig as creator and the config is
   *   rewritten to `newCreator` at 100%.
   * - **holder rewards**: `isHolderReward: true`, no `newCreator`. The
   *   creator becomes `holderRewardsPda(mint)`, cashback is cleared, a
   *   fee-shared coin's vaults are swept into that PDA's creator vault and
   *   its SharingConfig is terminated. Permanent: a later CTO on the coin may
   *   only repeat this path to change the rate (6083 otherwise). Needs
   *   `Global.isHolderRewardEnabled` (6084).
   *
   * `creatorFeeBps` may be set on either path, only on a quote admitted
   * through `QuoteControl` (6091 on SOL or a whitelisted quote), within
   * `1..=Global.maxConfigurableCreatorFeeBps` with the gate on (6078 / 6077),
   * and not on a coin that stays cashback (6080). Mayhem coins are refused
   * (6088). This builder encodes what it is given;
   * `OnlinePumpSdk.adminCtoInstructions` resolves the accounts from chain,
   * checks these rules up front and prepends the fee sweeps below.
   *
   * Un-swept creator fees block it: put `sweepCreatorFeeInstruction` (and,
   * on a graduated coin, `sweepPoolCreatorFeeInstruction`) first in the same
   * transaction, or it fails with 6095 `CreatorFeesNotSwept` (pump-amm 6081)
   * whenever v3 / pool v2 trades left creator fees behind.
   *
   * @param params.currentCreator - `bondingCurve.creator` as stored (the zero
   *   key on a legacy curve, the SharingConfig PDA on a fee-shared coin, the
   *   holder-rewards PDA on a holder-reward coin). Marked writable unless it
   *   is the zero key, so a wallet creator can be paid (6092 otherwise).
   * @param params.quoteMint - The curve's quote mint, `NATIVE_MINT` for a
   *   SOL-quoted or legacy curve (the program accepts WSOL for a curve that
   *   stores the zero key). Every quote ATA and the pool address derive from
   *   it and `quoteTokenProgram`, the program that owns the mint.
   */
  async adminCtoInstruction({
    adminSetCreatorAuthority,
    mint,
    currentCreator,
    quoteMint,
    quoteTokenProgram = TOKEN_PROGRAM_ID,
    isHolderReward,
    creatorFeeBps,
    newCreator,
  }: {
    adminSetCreatorAuthority: PublicKey;
    mint: PublicKey;
    currentCreator: PublicKey;
    quoteMint: PublicKey;
    quoteTokenProgram?: PublicKey;
    isHolderReward?: boolean;
    creatorFeeBps?: BN;
    newCreator?: PublicKey;
  }): Promise<TransactionInstruction> {
    const creatorVault = creatorVaultPda(currentCreator);
    const holderCreatorVault = creatorVaultPda(holderRewardsPda(mint));
    const coinCreatorVaultAuthority = ammCreatorVaultPda(currentCreator);
    const ata = (owner: PublicKey) =>
      quoteAta(owner, quoteMint, quoteTokenProgram);

    const instruction = await this.offlinePumpProgram.methods
      .adminCto(
        isHolderReward ?? null,
        creatorFeeBps ?? null,
        newCreator ?? null,
      )
      .accountsPartial({
        adminSetCreatorAuthority,
        global: GLOBAL_PDA,
        mint,
        quoteMint,
        quoteTokenProgram,
        associatedTokenProgram: ASSOCIATED_TOKEN_PROGRAM_ID,
        systemProgram: SystemProgram.programId,
        bondingCurve: bondingCurvePda(mint),
        currentCreator,
        currentCreatorQuoteTokenAccount: ata(currentCreator),
        creatorVault,
        creatorVaultQuoteTokenAccount: ata(creatorVault),
        holderCreatorVault,
        holderCreatorVaultQuoteTokenAccount: ata(holderCreatorVault),
        pumpAmm: PUMP_AMM_PROGRAM_ID,
        ammGlobalConfig: AMM_GLOBAL_CONFIG_PDA,
        poolAuthority: pumpPoolAuthorityPda(mint),
        pool: canonicalPumpPoolPdaWithQuote(mint, quoteMint),
        pumpAmmEventAuthority: PUMP_AMM_EVENT_AUTHORITY_PDA,
        coinCreatorVaultAuthority,
        coinCreatorVaultAta: ata(coinCreatorVaultAuthority),
        sharingConfig: feeSharingConfigPda(mint),
        pumpFees: PUMP_FEE_PROGRAM_ID,
        pumpFeesEventAuthority: PUMP_FEE_EVENT_AUTHORITY_PDA,
        eventAuthority: PUMP_EVENT_AUTHORITY_PDA,
        program: PUMP_PROGRAM_ID,
      })
      .instruction();

    // The IDL declares `current_creator` read-only (a legacy curve's zero-key
    // creator is the system program, whose write lock the runtime demotes);
    // the program requires a wallet creator to be passed writable so it can
    // be paid. Any other key may be writable too, so mark every non-zero key.
    if (!currentCreator.equals(PublicKey.default)) {
      for (const key of instruction.keys) {
        if (key.pubkey.equals(currentCreator)) {
          key.isWritable = true;
        }
      }
    }
    return instruction;
  }

  /**
   * `distribute_fee_to_holders`: pays the fees collected on a holder-reward
   * coin's `holderRewardsPda(mint)` out to holders. Signed by
   * `Global.holderRewardClaimAuthority`, who also pays the rent of any
   * recipient quote ATA created (token quotes only). `recipients[i].amount`
   * goes to `recipients[i].owner`: as lamports on a SOL quote, as tokens into
   * the owner's quote ATA (created if missing) on a token quote. The program
   * checks `amounts.length * 2 == remaining accounts` and each ATA (6085),
   * refuses to leave the PDA between zero and its rent-exempt minimum on a
   * SOL quote (6086; draining it fully is fine) and needs
   * `holderRewardsTokenAccount` on a token quote (6087).
   *
   * The fees reach the PDA through the permissionless collects with the PDA
   * as `creator`: `collect_creator_fee` / `collect_creator_fee_v2` on the
   * curve and, after graduation, pump-amm's `collect_coin_creator_fee` or
   * `transfer_creator_fees_to_pump`.
   *
   * @param params.holderRewardsTokenAccount - Any quote token account owned
   *   by the PDA, normally `quoteAta(holderRewardsPda(mint), quoteMint,
   *   quoteTokenProgram)`. The payout source on a token quote; on a SOL quote
   *   a parked WSOL account that is closed into the PDA first. Omit when
   *   there is none (SOL quote only).
   */
  async distributeFeeToHoldersInstruction({
    holderRewardClaimAuthority,
    mint,
    quoteMint,
    quoteTokenProgram = TOKEN_PROGRAM_ID,
    recipients,
    holderRewardsTokenAccount,
  }: {
    holderRewardClaimAuthority: PublicKey;
    mint: PublicKey;
    quoteMint: PublicKey;
    quoteTokenProgram?: PublicKey;
    recipients: readonly { owner: PublicKey; amount: BN }[];
    holderRewardsTokenAccount?: PublicKey;
  }): Promise<TransactionInstruction> {
    const isNative = quoteMint.equals(NATIVE_MINT);
    const remainingAccounts: AccountMeta[] = recipients.flatMap(({ owner }) => [
      // Lamports land on the owner; a token payout only reads it as the ATA's authority.
      { pubkey: owner, isSigner: false, isWritable: isNative },
      {
        pubkey: quoteAta(owner, quoteMint, quoteTokenProgram),
        isSigner: false,
        isWritable: !isNative,
      },
    ]);

    return await this.offlinePumpProgram.methods
      .distributeFeeToHolders(recipients.map(({ amount }) => amount))
      .accountsPartial({
        global: GLOBAL_PDA,
        holderRewardClaimAuthority,
        mint,
        holderRewards: holderRewardsPda(mint),
        holderRewardsTokenAccount: holderRewardsTokenAccount ?? null,
        quoteMint,
        quoteTokenProgram,
        associatedTokenProgram: ASSOCIATED_TOKEN_PROGRAM_ID,
        systemProgram: SystemProgram.programId,
        eventAuthority: PUMP_EVENT_AUTHORITY_PDA,
        program: PUMP_PROGRAM_ID,
      })
      .remainingAccounts(remainingAccounts)
      .instruction();
  }

  /**
   * pump-fees `set_exotic_flat_fees` on the pump `FeeConfig`
   * (`PUMP_FEE_CONFIG_PDA`): the flat schedule canonical curves and pools pay
   * when quoted in a mint that is neither SOL-like nor a listed stable (see
   * `selectCurveFeeSchedule`). `admin` signs, must be `FeeConfig.admin`, and
   * pays the rent top-up when the account still has the pre-exotic length.
   * All-zero fees mean unset: the program then charges `flatFees`.
   */
  async setExoticFlatFeesInstruction({
    admin,
    exoticFlatFees,
  }: {
    admin: PublicKey;
    exoticFlatFees: Fees;
  }): Promise<TransactionInstruction> {
    return await this.offlinePumpFeeProgram.methods
      .setExoticFlatFees(exoticFlatFees)
      .accountsPartial({ admin, configProgramId: PUMP_PROGRAM_ID })
      .instruction();
  }

  async getBuyInstructionRaw({
    user,
    mint,
    creator,
    amount,
    solAmount,
    feeRecipient = getStaticRandomFeeRecipient(),
    tokenProgram = TOKEN_PROGRAM_ID,
    buybackFeeRecipient = getStaticRandomFeeRecipientForBuyback(),
  }: {
    user: PublicKey;
    mint: PublicKey;
    creator: PublicKey;
    amount: BN;
    solAmount: BN;
    feeRecipient: PublicKey;
    tokenProgram?: PublicKey;
    buybackFeeRecipient: PublicKey;
  }): Promise<TransactionInstruction> {
    return await this.getBuyInstructionInternal({
      user,
      associatedUser: getAssociatedTokenAddressSync(
        mint,
        user,
        true,
        tokenProgram,
      ),
      mint,
      creator,
      feeRecipient,
      buybackFeeRecipient,
      amount,
      solAmount,
      tokenProgram,
    });
  }

  private async getBuyInstructionInternal({
    user,
    associatedUser,
    mint,
    creator,
    feeRecipient,
    buybackFeeRecipient,
    amount,
    solAmount,
    tokenProgram = TOKEN_PROGRAM_ID,
  }: {
    user: PublicKey;
    associatedUser: PublicKey;
    mint: PublicKey;
    creator: PublicKey;
    feeRecipient: PublicKey;
    buybackFeeRecipient: PublicKey;
    amount: BN;
    solAmount: BN;
    tokenProgram: PublicKey;
  }): Promise<TransactionInstruction> {
    return await this.offlinePumpProgram.methods
      .buy(amount, solAmount, { 0: true }, { 0: false })
      .accountsPartial({
        feeRecipient,
        mint,
        associatedUser,
        user,
        creatorVault: creatorVaultPda(creator),
        tokenProgram,
      })
      .remainingAccounts([
        {
          pubkey: bondingCurveV2Pda(mint),
          isWritable: false,
          isSigner: false,
        },
        {
          pubkey: buybackFeeRecipient,
          isWritable: true,
          isSigner: false,
        },
      ])
      .instruction();
  }

  async getSellInstructionRaw({
    user,
    mint,
    creator,
    amount,
    solAmount,
    feeRecipient = getStaticRandomFeeRecipient(),
    buybackFeeRecipient = getStaticRandomFeeRecipientForBuyback(),
    tokenProgram = TOKEN_PROGRAM_ID,
    cashback = false,
  }: {
    user: PublicKey;
    mint: PublicKey;
    creator: PublicKey;
    amount: BN;
    solAmount: BN;
    feeRecipient: PublicKey;
    buybackFeeRecipient: PublicKey;
    tokenProgram: PublicKey;
    cashback?: boolean;
  }): Promise<TransactionInstruction> {
    return await this.getSellInstructionInternal({
      user,
      mint,
      creator,
      feeRecipient,
      buybackFeeRecipient,
      amount,
      solAmount,
      tokenProgram,
      cashback,
    });
  }

  private async getSellInstructionInternal({
    user,
    mint,
    creator,
    feeRecipient,
    buybackFeeRecipient,
    amount,
    solAmount,
    tokenProgram,
    cashback,
  }: {
    user: PublicKey;
    mint: PublicKey;
    creator: PublicKey;
    feeRecipient: PublicKey;
    buybackFeeRecipient: PublicKey;
    amount: BN;
    solAmount: BN;
    tokenProgram: PublicKey;
    cashback?: boolean;
  }): Promise<TransactionInstruction> {
    const userVolumeAccumulator = userVolumeAccumulatorPda(user);
    const fixedRemaininAccounts = [
      {
        pubkey: bondingCurveV2Pda(mint),
        isWritable: false,
        isSigner: false,
      },
      {
        pubkey: buybackFeeRecipient,
        isWritable: true,
        isSigner: false,
      },
    ];
    return await this.offlinePumpProgram.methods
      .sell(amount, solAmount)
      .accountsPartial({
        feeRecipient,
        mint,
        associatedUser: getAssociatedTokenAddressSync(
          mint,
          user,
          true,
          tokenProgram,
        ),
        user,
        creatorVault: creatorVaultPda(creator),
        tokenProgram,
      })
      .remainingAccounts(
        cashback
          ? [
              {
                pubkey: userVolumeAccumulator,
                isWritable: true,
                isSigner: false,
              },
              ...fixedRemaininAccounts,
            ]
          : fixedRemaininAccounts,
      )
      .instruction();
  }

  async buyV2Instructions({
    global,
    bondingCurveAccountInfo,
    bondingCurve,
    associatedUserAccountInfo,
    mint,
    user,
    amount,
    quoteAmount,
    slippage,
    tokenProgram = TOKEN_2022_PROGRAM_ID,
    quoteTokenProgram = TOKEN_PROGRAM_ID,
  }: {
    global: Global;
    bondingCurveAccountInfo: AccountInfo<Buffer>;
    bondingCurve: BondingCurve;
    associatedUserAccountInfo: AccountInfo<Buffer> | null;
    mint: PublicKey;
    user: PublicKey;
    amount: BN;
    quoteAmount: BN;
    slippage: number;
    tokenProgram?: PublicKey;
    quoteTokenProgram?: PublicKey;
  }): Promise<TransactionInstruction[]> {
    const instructions: TransactionInstruction[] = [];

    const associatedUser = getAssociatedTokenAddressSync(
      mint,
      user,
      true,
      tokenProgram,
    );

    if (!associatedUserAccountInfo) {
      instructions.push(
        createAssociatedTokenAccountIdempotentInstruction(
          user,
          associatedUser,
          user,
          mint,
          tokenProgram,
        ),
      );
    }

    const quoteMint = isLegacyQuoteMint(bondingCurve.quoteMint)
      ? NATIVE_MINT
      : bondingCurve.quoteMint;

    instructions.push(
      await this.buyV2Instruction({
        global,
        mint,
        creator: bondingCurve.creator,
        user,
        associatedUser,
        amount,
        quoteAmount,
        slippage,
        tokenProgram,
        quoteMint,
        quoteTokenProgram,
        mayhemMode: bondingCurve.isMayhemMode,
      }),
    );

    return instructions;
  }

  /**
   * `create_v2` + the user's base ATA + a first `buy_v2`, all agreeing on the
   * quote. See `createV2Instruction` for the quote rules and the compute
   * budget to add (~500k CU for a token quote).
   *
   * @param params.quoteTokenProgram - The program that owns `quoteMint`; used
   *   by both the create and the buy. Defaults to `TOKEN_PROGRAM_ID` (SOL,
   *   USDC); `OnlinePumpSdk.fetchQuoteTokenProgram` resolves it.
   * @param params.creatorFeeBps - Forwarded to `createV2Instruction`. Unlike
   *   that builder this one holds `global`, so a nonzero rate the program
   *   would reject throws up front: `CreatorFeeNotConfigurableError` (gate
   *   off), `CreatorFeeBpsOutOfRangeError` (outside
   *   `1..=global.maxConfigurableCreatorFeeBps`). Quote `amount` with the same
   *   rate (`getBuyTokenAmountFromSolAmount`'s `creatorFeeBps`), or the buy's
   *   `quoteAmount` falls short of the fees the program charges.
   * @param params.holderReward - Forwarded to `createV2Instruction`; the buy
   *   then targets the holder-rewards PDA's creator vault, as the program
   *   does. Throws `HolderRewardDisabledError` while
   *   `global.isHolderRewardEnabled` is off.
   * @param params.cashback - Deprecated: throws `CashbackDeprecatedError`
   *   when `true`, as `create_v2` would fail with 6082.
   */
  async createV2AndBuyV2Instructions({
    global,
    mint,
    name,
    symbol,
    uri,
    creator,
    user,
    amount,
    quoteAmount,
    mayhemMode,
    cashback = false,
    quoteMint,
    quoteTokenProgram = TOKEN_PROGRAM_ID,
    creatorFeeBps,
    holderReward = false,
    pumpQuote,
    slippage = 1,
  }: {
    global: Global;
    mint: PublicKey;
    name: string;
    symbol: string;
    uri: string;
    creator: PublicKey;
    user: PublicKey;
    amount: BN;
    quoteAmount: BN;
    mayhemMode: boolean;
    /** @deprecated cashback coins can no longer be created (6082). */
    cashback?: boolean;
    quoteMint?: PublicKey;
    quoteTokenProgram?: PublicKey;
    creatorFeeBps?: BN;
    holderReward?: boolean;
    /** See `createV2Instruction`; for a pump-coin `quoteMint`. */
    pumpQuote?: PumpQuoteAccounts;
    /**
     * Percent added to `quoteAmount` for the buy's cost cap (default 1). A
     * pump-quoted coin's seed follows the quote coin's live price, so widen
     * it when that price may move before the transaction lands.
     */
    slippage?: number;
  }): Promise<TransactionInstruction[]> {
    assertCreateV2FlagsAllowed({
      global,
      mint,
      cashback,
      holderReward,
      creatorFeeBps,
    });
    const associatedUser = getAssociatedTokenAddressSync(
      mint,
      user,
      true,
      TOKEN_2022_PROGRAM_ID,
    );
    const { buyQuoteMint, buyQuoteTokenProgram } = createAndBuyQuote(
      quoteMint,
      quoteTokenProgram,
    );
    return [
      await this.createV2Instruction({
        mint,
        name,
        symbol,
        uri,
        creator,
        user,
        mayhemMode,
        cashback,
        quoteMint,
        quoteTokenProgram,
        creatorFeeBps,
        holderReward,
        pumpQuote,
      }),
      createAssociatedTokenAccountIdempotentInstruction(
        user,
        associatedUser,
        user,
        mint,
        TOKEN_2022_PROGRAM_ID,
      ),
      await this.buyV2Instruction({
        global,
        mint,
        creator: createdCurveCreator(mint, creator, holderReward),
        user,
        associatedUser,
        amount,
        quoteAmount,
        slippage,
        tokenProgram: TOKEN_2022_PROGRAM_ID,
        quoteMint: buyQuoteMint,
        quoteTokenProgram: buyQuoteTokenProgram,
        mayhemMode,
      }),
    ];
  }

  private async buyV2Instruction({
    global,
    mint,
    creator,
    user,
    associatedUser,
    amount,
    quoteAmount,
    slippage,
    tokenProgram = TOKEN_2022_PROGRAM_ID,
    quoteMint,
    quoteTokenProgram = TOKEN_PROGRAM_ID,
    mayhemMode = false,
  }: {
    global: Global;
    mint: PublicKey;
    creator: PublicKey;
    user: PublicKey;
    associatedUser: PublicKey;
    amount: BN;
    quoteAmount: BN;
    slippage: number;
    tokenProgram: PublicKey;
    quoteMint: PublicKey;
    quoteTokenProgram: PublicKey;
    mayhemMode: boolean;
  }) {
    return await this.getBuyV2InstructionInternal({
      user,
      associatedUser,
      mint,
      creator,
      feeRecipient: getFeeRecipient(global, mayhemMode),
      buybackFeeRecipient: getStaticRandomFeeRecipientForBuyback(),
      amount,
      quoteAmount: quoteAmount.add(
        quoteAmount.mul(new BN(Math.floor(slippage * 10))).div(new BN(1000)),
      ),
      tokenProgram,
      quoteMint,
      quoteTokenProgram,
    });
  }

  async sellV2Instructions({
    global,
    bondingCurveAccountInfo,
    bondingCurve,
    mint,
    user,
    amount,
    quoteAmount,
    slippage,
    tokenProgram = TOKEN_2022_PROGRAM_ID,
    quoteTokenProgram = TOKEN_PROGRAM_ID,
  }: {
    global: Global;
    bondingCurveAccountInfo: AccountInfo<Buffer>;
    bondingCurve: BondingCurve;
    mint: PublicKey;
    user: PublicKey;
    amount: BN;
    quoteAmount: BN;
    slippage: number;
    tokenProgram?: PublicKey;
    quoteTokenProgram?: PublicKey;
  }): Promise<TransactionInstruction[]> {
    const instructions: TransactionInstruction[] = [];

    const quoteMint = isLegacyQuoteMint(bondingCurve.quoteMint)
      ? NATIVE_MINT
      : bondingCurve.quoteMint;

    instructions.push(
      await this.getSellV2InstructionInternal({
        user,
        mint,
        creator: bondingCurve.creator,
        feeRecipient: getFeeRecipient(global, bondingCurve.isMayhemMode),
        buybackFeeRecipient: getStaticRandomFeeRecipientForBuyback(),
        amount,
        quoteAmount: quoteAmount.sub(
          quoteAmount.mul(new BN(Math.floor(slippage * 10))).div(new BN(1000)),
        ),
        tokenProgram,
        quoteMint,
        quoteTokenProgram,
      }),
    );

    return instructions;
  }

  async getBuyV2InstructionRaw({
    user,
    mint,
    creator,
    amount,
    quoteAmount,
    feeRecipient = getStaticRandomFeeRecipient(),
    buybackFeeRecipient = getStaticRandomFeeRecipientForBuyback(),
    tokenProgram = TOKEN_2022_PROGRAM_ID,
    quoteMint = NATIVE_MINT,
    quoteTokenProgram = TOKEN_PROGRAM_ID,
  }: {
    user: PublicKey;
    mint: PublicKey;
    creator: PublicKey;
    amount: BN;
    quoteAmount: BN;
    feeRecipient?: PublicKey;
    buybackFeeRecipient?: PublicKey;
    tokenProgram?: PublicKey;
    quoteMint?: PublicKey;
    quoteTokenProgram?: PublicKey;
  }): Promise<TransactionInstruction> {
    return await this.getBuyV2InstructionInternal({
      user,
      associatedUser: getAssociatedTokenAddressSync(
        mint,
        user,
        true,
        tokenProgram,
      ),
      mint,
      creator,
      feeRecipient,
      buybackFeeRecipient,
      amount,
      quoteAmount,
      tokenProgram,
      quoteMint,
      quoteTokenProgram,
    });
  }

  private async getBuyV2InstructionInternal({
    user,
    associatedUser,
    mint,
    creator,
    feeRecipient,
    buybackFeeRecipient,
    amount,
    quoteAmount,
    tokenProgram,
    quoteMint,
    quoteTokenProgram,
  }: {
    user: PublicKey;
    associatedUser: PublicKey;
    mint: PublicKey;
    creator: PublicKey;
    feeRecipient: PublicKey;
    buybackFeeRecipient: PublicKey;
    amount: BN;
    quoteAmount: BN;
    tokenProgram: PublicKey;
    quoteMint: PublicKey;
    quoteTokenProgram: PublicKey;
  }): Promise<TransactionInstruction> {
    const bondingCurve = bondingCurvePda(mint);
    const creatorVault = creatorVaultPda(creator);
    const userVolumeAccumulator = userVolumeAccumulatorPda(user);

    return await this.offlinePumpProgram.methods
      .buyV2(amount, quoteAmount, { 0: false })
      .accountsPartial({
        baseMint: mint,
        quoteMint,
        baseTokenProgram: tokenProgram,
        quoteTokenProgram,
        feeRecipient,
        associatedQuoteFeeRecipient: quoteAta(
          feeRecipient,
          quoteMint,
          quoteTokenProgram,
        ),
        buybackFeeRecipient,
        associatedQuoteBuybackFeeRecipient: quoteAta(
          buybackFeeRecipient,
          quoteMint,
          quoteTokenProgram,
        ),
        associatedBaseBondingCurve: getAssociatedTokenAddressSync(
          mint,
          bondingCurve,
          true,
          tokenProgram,
        ),
        associatedQuoteBondingCurve: quoteAta(
          bondingCurve,
          quoteMint,
          quoteTokenProgram,
        ),
        user,
        associatedBaseUser: associatedUser,
        associatedQuoteUser: quoteAta(user, quoteMint, quoteTokenProgram),
        creatorVault,
        associatedCreatorVault: quoteAta(
          creatorVault,
          quoteMint,
          quoteTokenProgram,
        ),
        associatedUserVolumeAccumulator: quoteAta(
          userVolumeAccumulator,
          quoteMint,
          quoteTokenProgram,
        ),
      })
      .instruction();
  }

  async getSellV2InstructionRaw({
    user,
    mint,
    creator,
    amount,
    quoteAmount,
    feeRecipient = getStaticRandomFeeRecipient(),
    buybackFeeRecipient = getStaticRandomFeeRecipientForBuyback(),
    tokenProgram = TOKEN_2022_PROGRAM_ID,
    quoteMint = NATIVE_MINT,
    quoteTokenProgram = TOKEN_PROGRAM_ID,
  }: {
    user: PublicKey;
    mint: PublicKey;
    creator: PublicKey;
    amount: BN;
    quoteAmount: BN;
    feeRecipient?: PublicKey;
    buybackFeeRecipient?: PublicKey;
    tokenProgram?: PublicKey;
    quoteMint?: PublicKey;
    quoteTokenProgram?: PublicKey;
  }): Promise<TransactionInstruction> {
    return await this.getSellV2InstructionInternal({
      user,
      mint,
      creator,
      feeRecipient,
      buybackFeeRecipient,
      amount,
      quoteAmount,
      tokenProgram,
      quoteMint,
      quoteTokenProgram,
    });
  }

  private async getSellV2InstructionInternal({
    user,
    mint,
    creator,
    feeRecipient,
    buybackFeeRecipient,
    amount,
    quoteAmount,
    tokenProgram,
    quoteMint,
    quoteTokenProgram,
  }: {
    user: PublicKey;
    mint: PublicKey;
    creator: PublicKey;
    feeRecipient: PublicKey;
    buybackFeeRecipient: PublicKey;
    amount: BN;
    quoteAmount: BN;
    tokenProgram: PublicKey;
    quoteMint: PublicKey;
    quoteTokenProgram: PublicKey;
  }): Promise<TransactionInstruction> {
    const bondingCurve = bondingCurvePda(mint);
    const creatorVault = creatorVaultPda(creator);
    const userVolumeAccumulator = userVolumeAccumulatorPda(user);

    return await this.offlinePumpProgram.methods
      .sellV2(amount, quoteAmount)
      .accountsPartial({
        baseMint: mint,
        quoteMint,
        baseTokenProgram: tokenProgram,
        quoteTokenProgram,
        feeRecipient,
        associatedQuoteFeeRecipient: quoteAta(
          feeRecipient,
          quoteMint,
          quoteTokenProgram,
        ),
        buybackFeeRecipient,
        associatedQuoteBuybackFeeRecipient: quoteAta(
          buybackFeeRecipient,
          quoteMint,
          quoteTokenProgram,
        ),
        associatedBaseBondingCurve: getAssociatedTokenAddressSync(
          mint,
          bondingCurve,
          true,
          tokenProgram,
        ),
        associatedQuoteBondingCurve: quoteAta(
          bondingCurve,
          quoteMint,
          quoteTokenProgram,
        ),
        user,
        associatedBaseUser: getAssociatedTokenAddressSync(
          mint,
          user,
          true,
          tokenProgram,
        ),
        associatedQuoteUser: quoteAta(user, quoteMint, quoteTokenProgram),
        creatorVault,
        associatedCreatorVault: quoteAta(
          creatorVault,
          quoteMint,
          quoteTokenProgram,
        ),
        associatedUserVolumeAccumulator: quoteAta(
          userVolumeAccumulator,
          quoteMint,
          quoteTokenProgram,
        ),
      })
      .instruction();
  }

  /**
   * `buy_v3`: buys `amount` tokens for at most `quoteAmount` plus `slippage`
   * percent. Prices and fees are the same as `buy_v2`
   * (`getBuySolAmountFromTokenAmount` quotes it), but only the buyback slice
   * of the protocol fee leaves in the trade: the rest of the protocol fee and
   * the creator fee stay on the curve (`BondingCurve.protocolFees` /
   * `creatorFee`) until `sweepProtocolFeeInstruction` /
   * `sweepCreatorFeeInstruction` pay them out. Creates the user's base ATA
   * when `associatedUserAccountInfo` is null and, on a token quote, the
   * buyback recipient's quote ATA when missing (idempotent; the user pays
   * its rent the first time, as the program never creates it).
   *
   * @param params.buybackFeeRecipient - The listed buyback wallet to pay
   *   (see `getBuyV3InstructionRaw`); defaults as there.
   *
   * A buy past the remaining supply completes the curve and buys the rest
   * from the pool the migration will create (the post-completion leg; a
   * `PostCompleteBuyEvent` follows `CompleteEvent`); quote it with
   * `getBuyV3QuoteAmountFromTokenAmount`. Every later trade is refused until
   * the migration.
   *
   * @param params.partialFill - Matters only where there is no
   *   post-completion leg (a mayhem curve): set, a buy past the remaining
   *   supply stops there; unset, it fails with 6021 `NotEnoughTokensToBuy`.
   * @throws {CashbackCoinNotSupportedError} for a cashback coin (6094); use
   *   `buyV2Instructions`.
   */
  async buyV3Instructions({
    bondingCurve,
    associatedUserAccountInfo,
    mint,
    user,
    amount,
    quoteAmount,
    slippage,
    tokenProgram = TOKEN_2022_PROGRAM_ID,
    quoteTokenProgram = TOKEN_PROGRAM_ID,
    partialFill = false,
    buybackFeeRecipient,
  }: {
    bondingCurve: BondingCurve;
    associatedUserAccountInfo: AccountInfo<Buffer> | null;
    mint: PublicKey;
    user: PublicKey;
    amount: BN;
    quoteAmount: BN;
    slippage: number;
    tokenProgram?: PublicKey;
    quoteTokenProgram?: PublicKey;
    partialFill?: boolean;
    buybackFeeRecipient?: PublicKey;
  }): Promise<TransactionInstruction[]> {
    if (bondingCurve.isCashbackCoin) {
      throw new CashbackCoinNotSupportedError(mint);
    }
    return [
      ...this.baseAtaInstructions(
        associatedUserAccountInfo,
        mint,
        user,
        tokenProgram,
      ),
      ...buybackAtaInstructions(
        user,
        bondingCurve.quoteMint,
        quoteTokenProgram,
        buybackFeeRecipient,
      ),
      await this.getBuyV3InstructionRaw({
        user,
        mint,
        amount,
        quoteAmount: quoteAmount.add(
          quoteAmount.mul(new BN(Math.floor(slippage * 10))).div(new BN(1000)),
        ),
        tokenProgram,
        quoteMint: bondingCurve.quoteMint,
        quoteTokenProgram,
        partialFill,
        buybackFeeRecipient,
      }),
    ];
  }

  /**
   * `buy_exact_quote_in_v3`: spends at most `quoteAmount` (fees included) and
   * requires at least `amount` tokens less `slippage` percent, `amount` being
   * the quote from `getBuyV3TokenAmountFromQuoteAmount`. Fees are kept as in
   * `buyV3Instructions`. A budget past the remaining supply completes the
   * curve and spends the rest in the pool-to-be; the minimum covers both
   * legs. Creates the user's base ATA when `associatedUserAccountInfo` is
   * null.
   *
   * @param params.partialFill - Matters only on a mayhem curve: set, a budget
   *   past the remaining supply buys what is left and skips the minimum;
   *   unset, it fails with 6021 `NotEnoughTokensToBuy`.
   * @throws {CashbackCoinNotSupportedError} for a cashback coin (6094).
   */
  async buyExactQuoteInV3Instructions({
    bondingCurve,
    associatedUserAccountInfo,
    mint,
    user,
    amount,
    quoteAmount,
    slippage,
    tokenProgram = TOKEN_2022_PROGRAM_ID,
    quoteTokenProgram = TOKEN_PROGRAM_ID,
    partialFill = false,
    buybackFeeRecipient,
  }: {
    bondingCurve: BondingCurve;
    associatedUserAccountInfo: AccountInfo<Buffer> | null;
    mint: PublicKey;
    user: PublicKey;
    amount: BN;
    quoteAmount: BN;
    slippage: number;
    tokenProgram?: PublicKey;
    quoteTokenProgram?: PublicKey;
    partialFill?: boolean;
    buybackFeeRecipient?: PublicKey;
  }): Promise<TransactionInstruction[]> {
    if (bondingCurve.isCashbackCoin) {
      throw new CashbackCoinNotSupportedError(mint);
    }
    return [
      ...this.baseAtaInstructions(
        associatedUserAccountInfo,
        mint,
        user,
        tokenProgram,
      ),
      ...buybackAtaInstructions(
        user,
        bondingCurve.quoteMint,
        quoteTokenProgram,
        buybackFeeRecipient,
      ),
      await this.getBuyExactQuoteInV3InstructionRaw({
        user,
        mint,
        spendableQuoteIn: quoteAmount,
        minTokensOut: lessSlippage(amount, slippage, 1),
        tokenProgram,
        quoteMint: bondingCurve.quoteMint,
        quoteTokenProgram,
        partialFill,
        buybackFeeRecipient,
      }),
    ];
  }

  /**
   * `sell_v3`: sells `amount` tokens for at least `quoteAmount` less
   * `slippage` percent. Prices and fees are the same as `sell_v2`; the
   * buyback slice leaves the curve in the trade, the rest of the fees stay on
   * it (see `buyV3Instructions`). On a token quote it first creates, when
   * missing, the seller's quote ATA and the buyback recipient's (idempotent).
   *
   * @throws {CashbackCoinNotSupportedError} for a cashback coin (6094); use
   *   `sellV2Instructions`.
   */
  async sellV3Instructions({
    bondingCurve,
    mint,
    user,
    amount,
    quoteAmount,
    slippage,
    tokenProgram = TOKEN_2022_PROGRAM_ID,
    quoteTokenProgram = TOKEN_PROGRAM_ID,
    buybackFeeRecipient,
  }: {
    bondingCurve: BondingCurve;
    mint: PublicKey;
    user: PublicKey;
    amount: BN;
    quoteAmount: BN;
    slippage: number;
    tokenProgram?: PublicKey;
    quoteTokenProgram?: PublicKey;
    buybackFeeRecipient?: PublicKey;
  }): Promise<TransactionInstruction[]> {
    if (bondingCurve.isCashbackCoin) {
      throw new CashbackCoinNotSupportedError(mint);
    }
    const quote = normalizeQuoteMint(bondingCurve.quoteMint);
    return [
      // On a token quote the proceeds go to the seller's quote ATA, which
      // must exist (it may not, say after a multi-hop buy).
      ...(isLegacyQuoteMint(quote)
        ? []
        : [
            createAssociatedTokenAccountIdempotentInstruction(
              user,
              quoteAta(user, quote, quoteTokenProgram),
              user,
              quote,
              quoteTokenProgram,
            ),
          ]),
      ...buybackAtaInstructions(
        user,
        bondingCurve.quoteMint,
        quoteTokenProgram,
        buybackFeeRecipient,
      ),
      await this.getSellV3InstructionRaw({
        user,
        mint,
        amount,
        quoteAmount: lessSlippage(quoteAmount, slippage),
        tokenProgram,
        quoteMint: bondingCurve.quoteMint,
        quoteTokenProgram,
        buybackFeeRecipient,
      }),
    ];
  }

  /**
   * `buy_v3` with `quoteAmount` as the exact `max_sol_cost` (fees included).
   *
   * @param params.quoteMint - The curve's quote mint; `bondingCurve.quoteMint`
   *   can be passed as is (the zero key is SOL).
   * @param params.buybackFeeRecipient - A listed `Global.buybackFeeRecipients`
   *   wallet. Passed as is on a SOL curve (a random listed one by default);
   *   on a token quote its `quoteMint` ATA is passed (the first listed one by
   *   default), which must already exist.
   */
  async getBuyV3InstructionRaw({
    user,
    mint,
    amount,
    quoteAmount,
    tokenProgram = TOKEN_2022_PROGRAM_ID,
    quoteMint = NATIVE_MINT,
    quoteTokenProgram = TOKEN_PROGRAM_ID,
    buybackFeeRecipient,
    partialFill = false,
  }: {
    user: PublicKey;
    mint: PublicKey;
    amount: BN;
    quoteAmount: BN;
    tokenProgram?: PublicKey;
    quoteMint?: PublicKey;
    quoteTokenProgram?: PublicKey;
    buybackFeeRecipient?: PublicKey;
    partialFill?: boolean;
  }): Promise<TransactionInstruction> {
    return await this.offlinePumpProgram.methods
      .buyV3(amount, quoteAmount, { 0: partialFill })
      .accountsPartial(
        tradeV3Accounts({
          user,
          mint,
          tokenProgram,
          quoteMint,
          quoteTokenProgram,
          buybackFeeRecipient,
        }),
      )
      .instruction();
  }

  /**
   * `buy_exact_quote_in_v3` with exact `spendable_quote_in` /
   * `min_tokens_out`. Accounts as in `getBuyV3InstructionRaw`.
   */
  async getBuyExactQuoteInV3InstructionRaw({
    user,
    mint,
    spendableQuoteIn,
    minTokensOut,
    tokenProgram = TOKEN_2022_PROGRAM_ID,
    quoteMint = NATIVE_MINT,
    quoteTokenProgram = TOKEN_PROGRAM_ID,
    buybackFeeRecipient,
    partialFill = false,
  }: {
    user: PublicKey;
    mint: PublicKey;
    spendableQuoteIn: BN;
    minTokensOut: BN;
    tokenProgram?: PublicKey;
    quoteMint?: PublicKey;
    quoteTokenProgram?: PublicKey;
    buybackFeeRecipient?: PublicKey;
    partialFill?: boolean;
  }): Promise<TransactionInstruction> {
    return await this.offlinePumpProgram.methods
      .buyExactQuoteInV3(spendableQuoteIn, minTokensOut, { 0: partialFill })
      .accountsPartial(
        tradeV3Accounts({
          user,
          mint,
          tokenProgram,
          quoteMint,
          quoteTokenProgram,
          buybackFeeRecipient,
        }),
      )
      .instruction();
  }

  /**
   * `sell_v3` with `quoteAmount` as the exact `min_sol_output` (net of
   * fees). Accounts as in `getBuyV3InstructionRaw`.
   */
  async getSellV3InstructionRaw({
    user,
    mint,
    amount,
    quoteAmount,
    tokenProgram = TOKEN_2022_PROGRAM_ID,
    quoteMint = NATIVE_MINT,
    quoteTokenProgram = TOKEN_PROGRAM_ID,
    buybackFeeRecipient,
  }: {
    user: PublicKey;
    mint: PublicKey;
    amount: BN;
    quoteAmount: BN;
    tokenProgram?: PublicKey;
    quoteMint?: PublicKey;
    quoteTokenProgram?: PublicKey;
    buybackFeeRecipient?: PublicKey;
  }): Promise<TransactionInstruction> {
    return await this.offlinePumpProgram.methods
      .sellV3(amount, quoteAmount)
      .accountsPartial(
        tradeV3Accounts({
          user,
          mint,
          tokenProgram,
          quoteMint,
          quoteTokenProgram,
          buybackFeeRecipient,
        }),
      )
      .instruction();
  }

  // An idempotent create of the user's base ATA when it is missing.
  private baseAtaInstructions(
    associatedUserAccountInfo: AccountInfo<Buffer> | null,
    mint: PublicKey,
    user: PublicKey,
    tokenProgram: PublicKey,
  ): TransactionInstruction[] {
    return associatedUserAccountInfo
      ? []
      : [
          createAssociatedTokenAccountIdempotentInstruction(
            user,
            getAssociatedTokenAddressSync(mint, user, true, tokenProgram),
            user,
            mint,
            tokenProgram,
          ),
        ];
  }

  /**
   * `sweep_protocol_fee`: pays the protocol fees v3 trades left on `mint`'s
   * curve (`BondingCurve.protocolFees`) to `recipient`, which must be a
   * `Global` fee recipient for the curve, never the zero key:
   * `getFeeRecipient(global, bondingCurve.isMayhemMode)`. Permissionless.
   * `payer` covers growing a pre-upgrade curve to `BONDING_CURVE_SIZE` and,
   * on a token quote, the recipient's quote ATA when it is missing. Nothing
   * moves when the bucket is empty. Works on completed and migrated curves.
   *
   * @param params.quoteMint - The curve's quote mint; `bondingCurve.quoteMint`
   *   can be passed as is (the zero key is SOL).
   */
  async sweepProtocolFeeInstruction({
    payer,
    mint,
    recipient,
    quoteMint,
    quoteTokenProgram = TOKEN_PROGRAM_ID,
  }: {
    payer: PublicKey;
    mint: PublicKey;
    recipient: PublicKey;
    quoteMint: PublicKey;
    quoteTokenProgram?: PublicKey;
  }): Promise<TransactionInstruction> {
    return await this.offlinePumpProgram.methods
      .sweepProtocolFee()
      .accountsPartial(
        sweepBondingCurveFeeAccounts({
          payer,
          mint,
          recipient,
          quoteMint,
          quoteTokenProgram,
        }),
      )
      .instruction();
  }

  /**
   * `sweep_creator_fee`: pays the creator fees v3 trades left on `mint`'s
   * curve (`BondingCurve.creatorFee`) to `creatorVaultPda(creator)`, where
   * `creator` is the curve's current `bondingCurve.creator` (a wallet, the
   * sharing config or the holder-rewards PDA). Permissionless; `payer` as in
   * `sweepProtocolFeeInstruction`, plus the vault's rent floor on SOL.
   *
   * Put it first, in the same transaction, in front of every
   * `distributeCreatorFees(V2)`, `adminCtoInstruction`,
   * `createFeeSharingConfig` and `updateFeeShares(V2)` on a coin that has
   * v3 trades: they fail with 6095 `CreatorFeesNotSwept` while the bucket is
   * nonzero. It is harmless when the bucket is empty.
   */
  async sweepCreatorFeeInstruction({
    payer,
    mint,
    creator,
    quoteMint,
    quoteTokenProgram = TOKEN_PROGRAM_ID,
  }: {
    payer: PublicKey;
    mint: PublicKey;
    creator: PublicKey;
    quoteMint: PublicKey;
    quoteTokenProgram?: PublicKey;
  }): Promise<TransactionInstruction> {
    return await this.offlinePumpProgram.methods
      .sweepCreatorFee()
      .accountsPartial(
        sweepBondingCurveFeeAccounts({
          payer,
          mint,
          recipient: creatorVaultPda(creator),
          quoteMint,
          quoteTokenProgram,
        }),
      )
      .instruction();
  }

  /**
   * pump-amm `sweep_creator_fee`: pays the creator fees the v2 pool trades
   * left in `mint`'s canonical pool (`Pool.creatorFees`) into the coin
   * creator vault of `coinCreator`, creating the vault's quote ATA when
   * missing (`payer` pays; also for growing a pre-upgrade pool).
   * Permissionless.
   *
   * `coinCreator` must be the pool's own `coin_creator` (read the pool
   * account: pump-swap-sdk's `decodePool`). It usually equals the curve's
   * `creator`, but not always (pump-amm's `set_coin_creator` can set it from
   * the metadata); any other key fails `ConstraintSeeds`, even with an empty
   * bucket. `OnlinePumpSdk` reads it for you.
   *
   * Put it first, in the same transaction, in front of `adminCtoInstruction`
   * and `createFeeSharingConfig` on a graduated coin (pump-amm 6081
   * `CreatorFeesNotSwept` otherwise), in front of `updateFeeShares(V2)`
   * (pump-fees 6033 `PoolCreatorFeesNotSwept`), and in front of
   * `transferCreatorFeesToPump(V2)` so a distribution includes those fees.
   */
  async sweepPoolCreatorFeeInstruction({
    payer,
    mint,
    coinCreator,
    quoteMint,
    quoteTokenProgram = TOKEN_PROGRAM_ID,
  }: {
    payer: PublicKey;
    mint: PublicKey;
    coinCreator: PublicKey;
    quoteMint: PublicKey;
    quoteTokenProgram?: PublicKey;
  }): Promise<TransactionInstruction> {
    const quote = normalizeQuoteMint(quoteMint);
    const pool = canonicalPumpPoolPdaWithQuote(mint, quote);
    const recipient = ammCreatorVaultPda(coinCreator);
    return await this.offlinePumpAmmProgram.methods
      .sweepCreatorFee()
      .accountsPartial({
        payer,
        globalConfig: AMM_GLOBAL_CONFIG_PDA,
        pool,
        quoteMint: quote,
        quoteTokenProgram,
        poolQuoteTokenAccount: quoteAta(pool, quote, quoteTokenProgram),
        recipient,
        recipientTokenAccount: quoteAta(recipient, quote, quoteTokenProgram),
        eventAuthority: PUMP_AMM_EVENT_AUTHORITY_PDA,
        program: PUMP_AMM_PROGRAM_ID,
      })
      .instruction();
  }

  /**
   * pump-amm `multi_hop_swap`: routes `amountIn` of the route's input mint
   * through `hops` (canonical pump pools and token-quoted pump curves, all
   * buys or all sells) into the output mint, exact-in, refusing less than
   * `minAmountOut` at the end. The protocol fee (with its buyback slice) is
   * charged once, at the leg trading the user's currency; the creator fee
   * (and a pool's LP fee) once, at the leg trading the coin at the far end;
   * middle hops charge nothing. A single hop pays what `buy_v2` / `sell_v2`
   * / `buy_v3` / `sell_v3` pay. Simulate for the amount out
   * (`OnlinePumpSdk.simulateMultiHopSwap`).
   *
   * Both user token accounts must exist (`multiHopSwapInstructions` creates
   * them and wraps / unwraps SOL). 16 fixed accounts plus 5 per hop: three
   * hops fit a legacy transaction, longer routes need a v0 transaction with a
   * lookup table. Budget compute generously (~200k CU per hop).
   *
   * @param params.buybackFeeRecipient - The listed buyback wallet whose ATA
   *   for the user's currency takes the slice (the first listed one by
   *   default). The ATA must exist.
   */
  async multiHopSwapInstruction({
    user,
    hops,
    side,
    amountIn,
    minAmountOut,
    buybackFeeRecipient,
  }: {
    user: PublicKey;
    hops: readonly MultiHopHop[];
    side: MultiHopSide;
    amountIn: BN;
    minAmountOut: BN;
    buybackFeeRecipient?: PublicKey;
  }): Promise<TransactionInstruction> {
    const { input, output, currency } = multiHopRouteEnds(hops, side);
    return await this.offlinePumpAmmProgram.methods
      .multiHopSwap(amountIn, minAmountOut)
      .accountsPartial({
        user,
        userInTokenAccount: quoteAta(user, input.mint, input.tokenProgram),
        userOutTokenAccount: quoteAta(user, output.mint, output.tokenProgram),
        buybackFeeRecipient: quoteAta(
          buybackFeeRecipient ?? getBuybackFeeRecipientForTokenQuote(),
          currency.mint,
          currency.tokenProgram,
        ),
        pumpGlobal: GLOBAL_PDA,
        pumpFeeConfig: PUMP_FEE_CONFIG_PDA,
        pumpEventAuthority: PUMP_EVENT_AUTHORITY_PDA,
      })
      .remainingAccounts(hops.flatMap(multiHopHopAccounts))
      .instruction();
  }

  /**
   * `multiHopSwapInstruction` with the user's accounts handled: idempotent
   * creates of the output token account (and of the input one when SOL is
   * wrapped; a token input must already hold `amountIn`) and of the buyback
   * recipient's ATA for the user's currency (the program never creates it;
   * the user pays its rent the first time), SOL wrapped into the WSOL
   * account first when the route starts at a WSOL pool, and the WSOL account
   * closed afterwards (returning its lamports, any WSOL it held before
   * included) when the input or the output is SOL. At a SOL-quoted curve end
   * the program moves SOL as lamports between the wallet and the curve (the
   * wallet must hold `amountIn` plus rent on a buy) and reads the WSOL
   * account only for its mint, so it is created but not funded.
   */
  async multiHopSwapInstructions(params: {
    user: PublicKey;
    hops: readonly MultiHopHop[];
    side: MultiHopSide;
    amountIn: BN;
    minAmountOut: BN;
    buybackFeeRecipient?: PublicKey;
  }): Promise<TransactionInstruction[]> {
    const { user } = params;
    const { input, output, currency } = multiHopRouteEnds(
      params.hops,
      params.side,
    );
    const ata = ({ mint, tokenProgram }: typeof input) =>
      quoteAta(user, mint, tokenProgram);
    const createAta = (end: typeof input) =>
      createAssociatedTokenAccountIdempotentInstruction(
        user,
        ata(end),
        user,
        end.mint,
        end.tokenProgram,
      );
    const closeWsol = (end: typeof input) =>
      end.mint.equals(NATIVE_MINT)
        ? [
            createCloseAccountInstruction(
              ata(end),
              user,
              user,
              [],
              end.tokenProgram,
            ),
          ]
        : [];
    // A token input must already hold `amountIn`; only SOL is handled here.
    // A route starting at a SOL-quoted curve takes `amountIn` from the wallet
    // as lamports and reads the WSOL account for its mint only: it must exist
    // but is not funded. A route starting at a WSOL pool pulls from it, so the
    // SOL is wrapped.
    const solIn = input.mint.equals(NATIVE_MINT);
    const wrapsInput = solIn && params.hops[0]?.venue === "pool";
    return [
      ...(solIn ? [createAta(input)] : []),
      ...(wrapsInput
        ? [
            SystemProgram.transfer({
              fromPubkey: user,
              toPubkey: ata(input),
              lamports: BigInt(params.amountIn.toString()),
            }),
            createSyncNativeInstruction(ata(input), input.tokenProgram),
          ]
        : []),
      createAta(output),
      ...buybackAtaInstructions(
        user,
        currency.mint,
        currency.tokenProgram,
        params.buybackFeeRecipient,
        true,
      ),
      await this.multiHopSwapInstruction(params),
      // Unwrap: the emptied input WSOL account, and SOL bought.
      ...closeWsol(input),
      ...closeWsol(output),
    ];
  }

  /**
   * Creates a fee sharing configuration for a token.
   *
   * Put `sweepCreatorFeeInstruction` (and, when `pool` is set,
   * `sweepPoolCreatorFeeInstruction`) first in the same transaction, so fees
   * that v3 / pool v2 trades left behind reach the current creator:
   * otherwise it fails with 6095 `CreatorFeesNotSwept` (pump-amm 6081).
   *
   * @param params - Parameters for creating a fee sharing configuration
   * @param params.creator - The creator of the token
   * @param params.mint - The mint address of the token
   * @param params.pool - The pool address of the token (null for ungraduated coins)
   */
  async createFeeSharingConfig({
    creator,
    mint,
    pool,
  }: {
    creator: PublicKey;
    mint: PublicKey;
    pool: PublicKey | null;
  }): Promise<TransactionInstruction> {
    return await this.offlinePumpFeeProgram.methods
      .createFeeSharingConfig()
      .accountsPartial({
        payer: creator,
        mint,
        pool,
      })
      .instruction();
  }

  /**
   * Updates the fee shares for a token's creator fee distribution.
   *
   * It distributes the pending fees first, so un-swept creator fees block
   * it: put `sweepCreatorFeeInstruction` (creator: the sharing config PDA)
   * first in the same transaction whenever v3 trades left creator fees on
   * the curve (pump 6095 `CreatorFeesNotSwept`), and
   * `sweepPoolCreatorFeeInstruction` whenever pump-amm v2 trades left some
   * in the coin's canonical WSOL pool (pump-fees 6033
   * `PoolCreatorFeesNotSwept`).
   *
   * The canonical WSOL pool goes last, after the shareholders: a complete
   * curve needs it there (the program reads it to check the pool's creator
   * bucket; it may not exist yet), a live curve ignores it. It is sent unless
   * `bondingCurveComplete` is `false`, which saves 33 bytes on a live curve
   * (sending it there is harmless; leaving it out on a complete curve is
   * refused).
   *
   * @param params - Parameters for updating fee shares
   * @param params.authority - The current authority that can modify the fee sharing config
   * @param params.mint - The mint address of the token
   * @param params.currentShareholders - Array of current shareholders
   * @param params.newShareholders - Array of new shareholders and their share percentages
   * @requirements for newShareholders:
   * - Must contain at least 1 shareholder (cannot be empty)
   * - Maximum of 10 shareholders allowed
   * - Each shareholder must have a positive share (shareBps > 0)
   * - Total shares must equal exactly 10,000 basis points (100%)
   * - No duplicate addresses allowed
   * - shareBps is in basis points where 1 bps = 0.01% (e.g., 1500 = 15%)
   * @throws {NoShareholdersError} If shareholders array is empty
   * @throws {TooManyShareholdersError} If more than 10 shareholders
   * @throws {ZeroShareError} If any shareholder has zero or negative shares
   * @throws {InvalidShareTotalError} If total shares don't equal 10,000 basis points
   * @throws {DuplicateShareholderError} If duplicate addresses are found
   * @example
   * ```typescript
   * const instruction = await PUMP_SDK.updateFeeShares({
   *   authority: authorityPublicKey,
   *   mint: mintPublicKey,
   *   curShareholders: [wallet1, wallet2, wallet3],
   *   newShareholders: [
   *     { address: wallet1, shareBps: 5000 }, // 50%
   *     { address: wallet2, shareBps: 3000 }, // 30%
   *     { address: wallet3, shareBps: 2000 }, // 20%
   *   ]
   * });
   * ```
   */
  async updateFeeShares({
    authority,
    mint,
    currentShareholders,
    newShareholders,
    bondingCurveComplete = true,
  }: {
    authority: PublicKey;
    mint: PublicKey;
    currentShareholders: PublicKey[];
    newShareholders: Shareholder[];
    bondingCurveComplete?: boolean;
  }): Promise<TransactionInstruction> {
    if (newShareholders.length === 0) {
      throw new NoShareholdersError();
    }

    if (newShareholders.length > MAX_SHAREHOLDERS) {
      throw new TooManyShareholdersError(
        newShareholders.length,
        MAX_SHAREHOLDERS,
      );
    }

    let totalShares = 0;
    const addresses = new Set<string>();

    for (const shareholder of newShareholders) {
      if (shareholder.shareBps <= 0) {
        throw new ZeroShareError(shareholder.address.toString());
      }

      totalShares += shareholder.shareBps;
      addresses.add(shareholder.address.toString());
    }

    if (totalShares !== 10_000) {
      throw new InvalidShareTotalError(totalShares);
    }

    if (addresses.size !== newShareholders.length) {
      throw new DuplicateShareholderError();
    }

    const sharingConfigPda = feeSharingConfigPda(mint);
    const coinCreatorVaultAuthority =
      coinCreatorVaultAuthorityPda(sharingConfigPda);

    return await this.offlinePumpFeeProgram.methods
      .updateFeeShares(
        newShareholders.map((sh) => ({
          address: sh.address,
          shareBps: sh.shareBps,
        })),
      )
      .accountsPartial({
        authority,
        mint,
        coinCreatorVaultAta: coinCreatorVaultAtaPda(
          coinCreatorVaultAuthority,
          NATIVE_MINT,
          TOKEN_PROGRAM_ID,
        ),
      })
      .remainingAccounts([
        ...currentShareholders.map((pubkey) => ({
          pubkey,
          isWritable: true,
          isSigner: false,
        })),
        ...(bondingCurveComplete
          ? [
              {
                pubkey: canonicalPumpPoolPda(mint),
                isWritable: false,
                isSigner: false,
              },
            ]
          : []),
      ])
      .instruction();
  }

  /**
   * Updates the fee shares for a token's creator fee distribution, for a coin
   * quoted in any mint. `updateFeeShares` (v1) only handles SOL-quoted coins;
   * a non-SOL coin must use this instruction so the pending fees it pays out
   * first move through the right quote ATAs. Needs the same sweeps first as
   * `updateFeeShares`, against the canonical pool of the curve's quote mint.
   *
   * @param params - Parameters for updating fee shares
   * @param params.authority - The current authority that can modify the fee sharing config
   * @param params.mint - The mint address of the token
   * @param params.currentShareholders - Array of current shareholders
   * @param params.newShareholders - Array of new shareholders and their share percentages
   * @param params.quoteMint - The coin's quote mint (`NATIVE_MINT` for SOL
   *   coins)
   * @param params.quoteTokenProgram - The program that owns `quoteMint`; every
   *   quote ATA (the vault's and each shareholder's) is derived with it. The
   *   `TOKEN_PROGRAM_ID` default is only right for SOL and USDC; pass the
   *   mint's owner (`OnlinePumpSdk.fetchQuoteTokenProgram`) for anything else.
   *   The canonical pool of `quoteMint`, which must be the curve's quote,
   *   goes last as on `updateFeeShares` (same `bondingCurveComplete`).
   * @requirements for newShareholders:
   * - Must contain at least 1 shareholder (cannot be empty)
   * - Maximum of 10 shareholders allowed
   * - Each shareholder must have a positive share (shareBps > 0)
   * - Total shares must equal exactly 10,000 basis points (100%)
   * - No duplicate addresses allowed
   * - shareBps is in basis points where 1 bps = 0.01% (e.g., 1500 = 15%)
   * @throws {NoShareholdersError} If shareholders array is empty
   * @throws {TooManyShareholdersError} If more than 10 shareholders
   * @throws {ZeroShareError} If any shareholder has zero or negative shares
   * @throws {InvalidShareTotalError} If total shares don't equal 10,000 basis points
   * @throws {DuplicateShareholderError} If duplicate addresses are found
   */
  async updateFeeSharesV2({
    authority,
    mint,
    currentShareholders,
    newShareholders,
    quoteMint,
    quoteTokenProgram = TOKEN_PROGRAM_ID,
    bondingCurveComplete = true,
  }: {
    authority: PublicKey;
    mint: PublicKey;
    currentShareholders: PublicKey[];
    newShareholders: Shareholder[];
    quoteMint: PublicKey;
    quoteTokenProgram: PublicKey;
    bondingCurveComplete?: boolean;
  }): Promise<TransactionInstruction> {
    // A SOL coin's curve stores the zero key; the instruction takes WSOL.
    quoteMint = normalizeQuoteMint(quoteMint);
    if (newShareholders.length === 0) {
      throw new NoShareholdersError();
    }

    if (newShareholders.length > MAX_SHAREHOLDERS) {
      throw new TooManyShareholdersError(
        newShareholders.length,
        MAX_SHAREHOLDERS,
      );
    }

    let totalShares = 0;
    const addresses = new Set<string>();

    for (const shareholder of newShareholders) {
      if (shareholder.shareBps <= 0) {
        throw new ZeroShareError(shareholder.address.toString());
      }

      totalShares += shareholder.shareBps;
      addresses.add(shareholder.address.toString());
    }

    if (totalShares !== 10_000) {
      throw new InvalidShareTotalError(totalShares);
    }

    if (addresses.size !== newShareholders.length) {
      throw new DuplicateShareholderError();
    }

    const sharingConfigPda = feeSharingConfigPda(mint);
    const coinCreatorVaultAuthority =
      coinCreatorVaultAuthorityPda(sharingConfigPda);
    const remainingAccounts = [
      ...currentShareholders.map((pubkey) => ({
        pubkey,
        isWritable: true,
        isSigner: false,
      })),
      ...(quoteMint.equals(NATIVE_MINT)
        ? []
        : currentShareholders.map((pubkey) => ({
            pubkey: getAssociatedTokenAddressSync(
              quoteMint,
              pubkey,
              true,
              quoteTokenProgram,
            ),
            isWritable: true,
            isSigner: false,
          }))),
      // Last, after every shareholder account: the pool of the curve's own
      // quote (WSOL for a SOL curve), read only on a complete curve.
      ...(bondingCurveComplete
        ? [
            {
              pubkey: canonicalPumpPoolPdaWithQuote(
                mint,
                normalizeQuoteMint(quoteMint),
              ),
              isWritable: false,
              isSigner: false,
            },
          ]
        : []),
    ];
    return await this.offlinePumpFeeProgram.methods
      .updateFeeSharesV2(
        newShareholders.map((sh) => ({
          address: sh.address,
          shareBps: sh.shareBps,
        })),
      )
      .accountsPartial({
        authority,
        mint,
        coinCreatorVaultAta: coinCreatorVaultAtaPda(
          coinCreatorVaultAuthority,
          quoteMint,
          quoteTokenProgram,
        ),
        quoteMint,
        tokenProgram: quoteTokenProgram,
        associatedTokenProgram: ASSOCIATED_TOKEN_PROGRAM_ID,
        systemProgram: SystemProgram.programId,
      })
      .remainingAccounts([...remainingAccounts])
      .instruction();
  }

  /**
   * Sweeps coin creator fees that have accrued on the Pump AMM into the
   * bonding curve creator vault, so they can later be paid out via
   * `distributeCreatorFeesV2`. Permissionless.
   *
   * For wrapped-SOL quotes the instruction closes & recreates the AMM coin
   * creator vault ATA and forwards the unwrapped lamports to `pump_creator_vault`.
   * For non-native quotes it does a token transfer between ATAs and creates
   * the destination `pump_creator_vault_ata` on the fly if it does not exist
   * (rent paid by `payer`).
   *
   * Assumes the coin has been opted into fee sharing (i.e. `coin_creator` on
   * the AMM pool is the `sharing_config` PDA for `mint`).
   *
   * @param params - Parameters for the transfer
   * @param params.payer - Transaction signer. Pays the rent for `pump_creator_vault_ata` when it has to be initialized (non-WSOL quotes only).
   * @param params.mint - The mint address of the token. Used to derive the sharing_config PDA, which is the coin creator post-migration.
   * @param params.quoteMint - The quote mint of the coin (use `NATIVE_MINT` for SOL-paired coins).
   * @param params.quoteTokenProgram - The program that owns `quoteMint`; both
   *   vault ATAs are derived with it. The `TOKEN_PROGRAM_ID` default is only
   *   right for SOL and USDC; pass the mint's owner
   *   (`OnlinePumpSdk.fetchQuoteTokenProgram`) for a Token-2022 quote.
   */
  async transferCreatorFeesToPumpV2({
    payer,
    mint,
    quoteMint,
    quoteTokenProgram = TOKEN_PROGRAM_ID,
  }: {
    payer: PublicKey;
    mint: PublicKey;
    quoteMint: PublicKey;
    quoteTokenProgram: PublicKey;
  }): Promise<TransactionInstruction> {
    const sharingConfigPda = feeSharingConfigPda(mint);

    return await this.offlinePumpAmmProgram.methods
      .transferCreatorFeesToPumpV2()
      .accountsPartial({
        payer,
        quoteMint,
        tokenProgram: quoteTokenProgram,
        coinCreator: sharingConfigPda,
      })
      .instruction();
  }

  decodeDistributeCreatorFeesEvent(data: Buffer): DistributeCreatorFeesEvent {
    return this.offlinePumpProgram.coder.types.decode<DistributeCreatorFeesEvent>(
      "distributeCreatorFeesEvent",
      data,
    );
  }

  /**
   * Distributes a SOL coin's creator vault to its shareholders. Put
   * `sweepCreatorFeeInstruction` (creator: `sharingConfigAddress`) first in
   * the same transaction: it fails with 6095 `CreatorFeesNotSwept` while v3
   * trades have creator fees on the curve.
   * `OnlinePumpSdk.buildDistributeCreatorFeesInstructions` does both.
   */
  async distributeCreatorFees({
    mint,
    sharingConfig,
    sharingConfigAddress,
  }: {
    mint: PublicKey;
    sharingConfig: SharingConfig;
    sharingConfigAddress: PublicKey;
  }): Promise<TransactionInstruction> {
    return await this.offlinePumpProgram.methods
      .distributeCreatorFees()
      .accountsPartial({
        mint,
        creatorVault: creatorVaultPda(sharingConfigAddress),
      })
      .remainingAccounts(
        sharingConfig.shareholders.map((shareholder) => ({
          pubkey: shareholder.address,
          isWritable: true,
          isSigner: false,
        })),
      )
      .instruction();
  }

  /**
   * Distributes a coin's accrued creator fees to its sharing-config
   * shareholders, for a coin quoted in any mint (`distributeCreatorFees` is
   * SOL-only). For a non-SOL quote the program pays each shareholder's ATA
   * and, with `shouldInitializeAta`, creates missing ones at `payer`'s cost.
   * Needs `sweepCreatorFeeInstruction` first, as `distributeCreatorFees`
   * does.
   *
   * @param params.quoteMint - The coin's quote mint (`NATIVE_MINT` for SOL
   *   coins).
   * @param params.quoteTokenProgram - The program that owns `quoteMint`; the
   *   vault's and every shareholder's quote ATA is derived with it. The
   *   `TOKEN_PROGRAM_ID` default is only right for SOL and USDC; pass the
   *   mint's owner (`OnlinePumpSdk.fetchQuoteTokenProgram`) for anything else.
   */
  async distributeCreatorFeesV2({
    mint,
    sharingConfig,
    sharingConfigAddress,
    quoteMint,
    payer,
    shouldInitializeAta = true,
    quoteTokenProgram = TOKEN_PROGRAM_ID,
  }: {
    mint: PublicKey;
    sharingConfig: SharingConfig;
    sharingConfigAddress: PublicKey;
    quoteMint: PublicKey;
    payer: PublicKey;
    shouldInitializeAta: boolean;
    quoteTokenProgram: PublicKey;
  }): Promise<TransactionInstruction> {
    const remainingAccounts = sharingConfig.shareholders.map((shareholder) => ({
      pubkey: shareholder.address,
      isWritable: true,
      isSigner: false,
    }));
    if (!quoteMint.equals(NATIVE_MINT)) {
      remainingAccounts.push(
        ...sharingConfig.shareholders.map((shareholder) => ({
          pubkey: getAssociatedTokenAddressSync(
            quoteMint,
            shareholder.address,
            true,
            quoteTokenProgram,
          ),
          isWritable: true,
          isSigner: false,
        })),
      );
    }
    return await this.offlinePumpProgram.methods
      .distributeCreatorFeesV2(shouldInitializeAta)
      .accountsPartial({
        mint,
        creatorVault: creatorVaultPda(sharingConfigAddress),
        quoteMint,
        quoteTokenProgram,
        associatedTokenProgram: ASSOCIATED_TOKEN_PROGRAM_ID,
        systemProgram: SystemProgram.programId,
        payer,
      })
      .remainingAccounts([...remainingAccounts])
      .instruction();
  }

  decodeMinimumDistributableFee(data: Buffer): MinimumDistributableFeeEvent {
    return this.offlinePumpProgram.coder.types.decode<MinimumDistributableFeeEvent>(
      "minimumDistributableFeeEvent",
      data,
    );
  }

  async getMinimumDistributableFee({
    mint,
    sharingConfig,
    sharingConfigAddress,
  }: {
    mint: PublicKey;
    sharingConfig: SharingConfig;
    sharingConfigAddress: PublicKey;
  }): Promise<TransactionInstruction> {
    return await this.offlinePumpProgram.methods
      .getMinimumDistributableFee()
      .accountsPartial({
        mint,
        creatorVault: creatorVaultPda(sharingConfigAddress),
      })
      .remainingAccounts(
        sharingConfig.shareholders.map((shareholder) => ({
          pubkey: shareholder.address,
          isWritable: true,
          isSigner: false,
        })),
      )
      .instruction();
  }

  /**
   * Creates a `DonationFeePda` for a `(mint, configId)` pair under the
   * pump-fees program. This PDA is the on-chain fee destination used when
   * routing a slice of creator fees to a donate.gg config; once created, you
   * can pass `donationFeePda(mint)` as a shareholder address in a
   * subsequent `updateFeeShares` call.
   *
   * The instruction is idempotent.
   *
   * @param params - Parameters for creating the donation fee PDA
   * @param params.coinCreator - The coin creator wallet; signs and pays rent
   *   for the new PDA. This is either the bonding curve's `creator`
   *   or the canonical pump-amm pool's `coin_creator`
   *   or the sharing_config.admin.
   * @param params.mint - Base mint of the coin whose creator fees are routed.
   * @param params.configId - The donate.gg config id this PDA escrows for.
   * @param params.quoteMint - The quote mint of the coin. You can pass
   *   `bondingCurve.quoteMint` directly: it is normalized via
   *   `normalizeQuoteMint`, so `PublicKey.default` (stored by legacy SOL
   *   coins) and `undefined` both resolve to `NATIVE_MINT`. Required for
   *   graduated non-SOL-quote coins: the canonical pool PDA is seeded by
   *   quote mint, so passing the wrong quote derives a nonexistent pool and
   *   the program rejects with `InvalidPool`. Ignored by the program for
   *   ungraduated coins.
   */
  async createDonationFeePda({
    coinCreator,
    mint,
    configId,
    quoteMint,
  }: {
    coinCreator: PublicKey;
    mint: PublicKey;
    configId: PublicKey;
    quoteMint?: PublicKey;
  }): Promise<TransactionInstruction> {
    return await this.offlinePumpFeeProgram.methods
      .createDonationFeePda()
      .accountsPartial({
        payer: coinCreator,
        configId,
        baseMint: mint,
        pool: canonicalPumpPoolPdaWithQuote(
          mint,
          normalizeQuoteMint(quoteMint),
        ),
        donationFeePda: donationFeePda(mint, configId),
      })
      .instruction();
  }

  /**
   * Cranks a previously-created `DonationFeePda`, forwarding its full
   * `donationFeePdaAta` balance into the donation relay program's debouncer
   * for the relayer to settle later.
   *
   * The instruction is **permissionless** — anyone can call it, paying the
   * tx fee (and rent for the WSOL ATA on first crank). The pump-fees handler
   * also wraps any bare lamports sitting on the `DonationFeePda` into its
   * WSOL ATA before forwarding (native quote path), so the only state needed
   * to crank is the `(mint, configId)` pair (the `configId` is read back from
   * the PDA by the relay CPI, but the caller still needs it to derive the
   * relay-side epoch_tracker / debouncer PDAs).
   *
   * Quote mint defaults to wrapped SOL (`NATIVE_MINT`). If/when other quote
   * mints are supported, override `quoteMint` to match the value stored on
   * the on-chain `DonationFeePda.quote_mint` (the program enforces equality
   * and will error otherwise).
   *
   * @param params - Parameters for cranking the donation fee PDA
   * @param params.payer - Wallet that signs and pays for `init_if_needed` ATAs.
   * @param params.mint - Base mint of the coin (the one whose creator fees
   *   feed the PDA — matches `DonationFeePda.base_mint`).
   * @param params.configId - The 32-byte donate.gg config id bound to the
   *   PDA; used to derive the relay's epoch tracker and debouncer PDAs.
   * @param params.donationRelayProgramId - Program id of the Donation Relay
   *   program for the target cluster (e.g. `DONATION_RELAY_PROGRAM_ID_MAINNET`
   *   or `DONATION_RELAY_PROGRAM_ID_DEVNET`).
   * @param params.quoteMint - Quote mint that the relay debounces in. Defaults
   *   to `NATIVE_MINT` (WSOL). Must equal `DonationFeePda.quote_mint`.
   */
  async crankDonationFeePda({
    payer,
    mint,
    configId,
    donationRelayProgramId,
    quoteMint = NATIVE_MINT,
  }: {
    payer: PublicKey;
    mint: PublicKey;
    configId: PublicKey;
    donationRelayProgramId: PublicKey;
    quoteMint?: PublicKey;
  }): Promise<TransactionInstruction> {
    const donationFeePdaAddress = donationFeePda(mint, configId);
    const epochTracker = donationRelayEpochTrackerPda(
      configId,
      quoteMint,
      donationRelayProgramId,
    );
    const debouncer = donationRelayDebouncerPda(
      configId,
      quoteMint,
      donationRelayProgramId,
    );

    return await this.offlinePumpFeeProgram.methods
      .crankDonationFeePda()
      .accountsPartial({
        payer,
        donationFeePda: donationFeePdaAddress,
        quoteMint,
        donationFeePdaAta: getAssociatedTokenAddressSync(
          quoteMint,
          donationFeePdaAddress,
          true,
          TOKEN_PROGRAM_ID,
        ),
        donationRelayProgram: donationRelayProgramId,
        donationRelayEventAuthority: donationRelayEventAuthorityPda(
          donationRelayProgramId,
        ),
        mintWhitelist: donationRelayMintWhitelistPda(donationRelayProgramId),
        epochTracker,
        debouncer,
        debouncerAta: getAssociatedTokenAddressSync(
          quoteMint,
          debouncer,
          true,
          TOKEN_PROGRAM_ID,
        ),
      })
      .instruction();
  }

  /**
   * Creates a social fee PDA that can accumulate fees for a social media user.
   *
   * @param params - Parameters for creating the social fee PDA
   * @param params.payer - The account paying for the transaction
   * @param params.userId - The user ID string (max 20 characters, typically the numeric social media user ID)
   * @param params.platform - Platform identifier (0=pump, 1=X, etc.)
   */
  async createSocialFeePda({
    payer,
    userId,
    platform,
  }: {
    payer: PublicKey;
    userId: string;
    platform: number;
  }): Promise<TransactionInstruction> {
    return await this.offlinePumpFeeProgram.methods
      .createSocialFeePda(userId, platform)
      .accountsPartial({
        payer,
        socialFeePda: socialFeePda(userId, platform),
      })
      .instruction();
  }

  // Internal use only
  async claimSocialFeePda({
    recipient,
    socialClaimAuthority,
    userId,
    platform,
  }: {
    recipient: PublicKey;
    socialClaimAuthority: PublicKey;
    userId: string;
    platform: number;
  }): Promise<TransactionInstruction> {
    return await this.offlinePumpFeeProgram.methods
      .claimSocialFeePda(userId, platform)
      .accountsPartial({
        recipient,
        socialFeePda: socialFeePda(userId, platform),
        socialClaimAuthority,
      })
      .instruction();
  }

  async claimCashbackInstruction({
    user,
  }: {
    user: PublicKey;
  }): Promise<TransactionInstruction> {
    return await this.offlinePumpProgram.methods
      .claimCashback()
      .accountsPartial({
        user,
      })
      .instruction();
  }

  /**
   * `claim_cashback_v2`: pays out the cashback a user accrued in `quoteMint`
   * from their volume accumulator's quote ATA to their own quote ATA.
   *
   * @param params.quoteMint - The quote the cashback accrued in; defaults to
   *   `NATIVE_MINT` (SOL).
   * @param params.quoteTokenProgram - The program that owns `quoteMint`; both
   *   ATAs are derived with it. The `TOKEN_PROGRAM_ID` default is only right
   *   for SOL and USDC; pass the mint's owner
   *   (`OnlinePumpSdk.fetchQuoteTokenProgram`) for a Token-2022 quote.
   */
  async claimCashbackV2Instruction({
    user,
    quoteMint = NATIVE_MINT,
    quoteTokenProgram = TOKEN_PROGRAM_ID,
  }: {
    user: PublicKey;
    quoteMint?: PublicKey;
    quoteTokenProgram?: PublicKey;
  }): Promise<TransactionInstruction> {
    const userVolumeAccumulator = userVolumeAccumulatorPda(user);

    return await this.offlinePumpProgram.methods
      .claimCashbackV2()
      .accountsPartial({
        user,
        quoteMint,
        quoteTokenProgram,
        associatedUserVolumeAccumulator: quoteAta(
          userVolumeAccumulator,
          quoteMint,
          quoteTokenProgram,
        ),
        associatedQuoteUser: quoteAta(user, quoteMint, quoteTokenProgram),
      })
      .instruction();
  }
}

export const PUMP_SDK = new PumpSdk();

/**
 * Checks if a creator has migrated to using a fee sharing configuration.
 *
 * When a creator sets up fee sharing, the creator address in the BondingCurve or Pool
 * is replaced with the fee sharing config PDA address. This function checks if that
 * migration has occurred.
 *
 * @param params - Parameters for checking migration status
 * @param params.mint - The mint address of the token
 * @param params.creator - The creator address to check
 *                         - For ungraduated coins: use BondingCurve.creator
 *                         - For graduated coins: use Pool.coinCreator (from AMM pool)
 * @returns true if the creator has migrated to fee sharing config, false otherwise
 * @example
 * ```typescript
 * import { hasCoinCreatorMigratedToSharingConfig } from "@pump-fun/sdk";
 *
 * // For an ungraduated coin. OnlinePumpSdk reads the curve through
 * // PumpSdk.decodeBondingCurve, which accepts every live curve length;
 * // Anchor's `program.account.bondingCurve.fetch` throws on the 115-byte
 * // curves under the current IDL.
 * const bondingCurve = await onlineSdk.fetchBondingCurve(mint);
 * const hasMigrated = hasCoinCreatorMigratedToSharingConfig({
 *   mint,
 *   creator: bondingCurve.creator
 * });
 *
 * // For a graduated coin, with `pool` decoded by pump-swap-sdk's padded
 * // `Pool` reader (`ammProgram.account.pool.fetch` likewise throws on the
 * // 261-byte live pools).
 * const hasMigrated = hasCoinCreatorMigratedToSharingConfig({
 *   mint,
 *   creator: pool.coinCreator
 * });
 *
 * if (hasMigrated) {
 *   // Creator fees are distributed according to fee sharing config
 * } else {
 *   // Creator fees go directly to the creator address
 * }
 * ```
 */
export function hasCoinCreatorMigratedToSharingConfig({
  mint,
  creator,
}: {
  mint: PublicKey;
  creator: PublicKey;
}): boolean {
  return feeSharingConfigPda(mint).equals(creator);
}

/**
 * Checks whether a sharing config reward split is editable.
 *
 * Reward split is NOT editable when:
 * - sharing config version is 1
 * - sharing config version is 2 but the admin authority has been revoked
 *
 * @param params - Parameters for editability check
 * @param params.sharingConfig - Sharing config account state
 * @returns true if reward split can be edited, false otherwise
 */
export function isSharingConfigEditable({
  sharingConfig,
}: {
  sharingConfig: SharingConfig;
}): boolean {
  if (sharingConfig.version === 1) {
    return false;
  }

  if (sharingConfig.version === 2 && sharingConfig.adminRevoked) {
    return false;
  }

  return true;
}
