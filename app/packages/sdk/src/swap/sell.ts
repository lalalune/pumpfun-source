import { RawMint } from "@solana/spl-token";
import { PublicKey } from "@solana/web3.js";
import BN from "bn.js";

import { computeFeesBps } from "./fees";
import {
  grossForTransferFee,
  netOfTransferFee,
  QuoteTransferFee,
} from "./transferFee";
import {
  GlobalConfig,
  FeeConfig,
  SellBaseInputResult,
  SellQuoteInputResult,
} from "./types";
import { minAfterSlippage } from "./slippage";
import { ceilDiv, fee } from "./util";

export function sellBaseInput({
  base,
  slippage,
  baseReserve,
  quoteReserve,
  virtualQuoteReserves = new BN(0),
  feeBucketsTotal = new BN(0),
  globalConfig,
  baseMintAccount,
  baseMint,
  coinCreator,
  creator,
  feeConfig,
  quoteMint,
  isMayhemMode,
  creatorFeeBps,
  quoteTransferFee,
}: {
  base: BN;
  slippage: number; // e.g. 1 => 1% slippage tolerance
  baseReserve: BN;
  quoteReserve: BN;
  virtualQuoteReserves?: BN;
  /**
   * `Pool.protocolFees + Pool.creatorFees`: fees v2 trades left in the quote vault. The program
   * pays sells only from `quoteReserve - feeBucketsTotal` (`real_quote_reserves`). Defaults to 0
   * (no fees accrued).
   */
  feeBucketsTotal?: BN;
  globalConfig: GlobalConfig;
  baseMintAccount: RawMint;
  baseMint: PublicKey;
  coinCreator: PublicKey;
  creator: PublicKey;
  feeConfig: FeeConfig | null;
  /**
   * `Pool.quoteMint`; selects the fee schedule (SOL-like -> feeTiers, USDC -> stableFeeTiers,
   * anything else -> exoticFlatFees, or flatFees while the exotic schedule is unset). Defaults to
   * WSOL: omitting it on a non-SOL pool prices with the SOL schedule.
   */
  quoteMint?: PublicKey;
  /** `Pool.isMayhemMode`; defaults to false. */
  isMayhemMode?: boolean;
  /**
   * `Pool.creatorFeeBps`; replaces the schedule's creator rate while
   * `globalConfig.creatorFeeConfigurable` is on and it is nonzero. Omitting it (or 0) prices with
   * the schedule, as before.
   */
  creatorFeeBps?: BN;
  /**
   * The quote mint's Token-2022 transfer fee this epoch (`SwapSolanaState.quoteTransferFee`).
   * The pool pays out as it is; `uiQuote` and `minQuote` are what lands in the wallet.
   */
  quoteTransferFee?: QuoteTransferFee | null;
}): SellBaseInputResult {
  // -----------------------------------------
  // 1) Basic validations
  // -----------------------------------------
  if (baseReserve.isZero() || quoteReserve.isZero()) {
    throw new Error(
      "Invalid input: 'baseReserve' or 'quoteReserve' cannot be zero.",
    );
  }

  // -----------------------------------------
  // 2) Calculate the raw quote output (no fees)
  //    This matches a typical constant-product formula for selling base to get quote:
  //      quote_amount_out = floor( (quoteReserve * base) / (baseReserve + base) )
  // -----------------------------------------
  const effectiveQuoteReserve = quoteReserve.add(virtualQuoteReserves);

  const quoteAmountOut = effectiveQuoteReserve
    .mul(base)
    .div(baseReserve.add(base)); // floor by BN.div

  // -----------------------------------------
  // 3) Calculate fees
  //    LP fee and protocol fee are both taken from 'quoteAmountOut'
  // -----------------------------------------
  const {
    lpFeeBps,
    protocolFeeBps,
    creatorFeeBps: coinCreatorFeeBps,
  } = computeFeesBps({
    globalConfig,
    feeConfig,
    creator,
    baseMintSupply: new BN(baseMintAccount.supply.toString()),
    baseMint,
    baseReserve,
    quoteReserve: effectiveQuoteReserve,
    quoteMint,
    isMayhemMode,
    creatorFeeBps,
  });

  const lpFee = fee(quoteAmountOut, lpFeeBps);
  const protocolFee = fee(quoteAmountOut, protocolFeeBps);
  const coinCreatorFee = PublicKey.default.equals(coinCreator)
    ? new BN(0)
    : fee(quoteAmountOut, coinCreatorFeeBps);

  const { userQuoteAmountOut } = sellAmounts(
    quoteAmountOut,
    { lpFee, protocolFee, coinCreatorFee },
    quoteReserve.sub(feeBucketsTotal),
  );
  const finalQuote = netOfTransferFee(quoteTransferFee, userQuoteAmountOut);
  if (finalQuote.isNeg()) {
    // Theoretically shouldn't happen unless fees exceed quoteAmountOut
    throw new Error("Fees exceed total output; final quote is negative.");
  }

  // -----------------------------------------
  // 4) Calculate minQuote with slippage
  //    - If slippage=1 => 1%, we allow receiving as low as 99% of finalQuote
  // -----------------------------------------
  const minQuote = minAfterSlippage(finalQuote, slippage);

  return {
    uiQuote: finalQuote, // actual tokens user receives after fees
    minQuote, // minimum acceptable tokens after applying slippage
    internalQuoteAmountOut: quoteAmountOut,
  };
}

/**
 * A sell's gross quote split: what leaves the reserves once the LP fee stays (which real
 * reserves, the vault net of the fee buckets, must cover) and the seller's share once the
 * protocol and creator fees stay too.
 *
 * rust reference: pump-amm trade_v2 sell_amounts()
 */
export function sellAmounts(
  quoteAmountOut: BN,
  fees: { lpFee: BN; protocolFee: BN; coinCreatorFee: BN },
  realQuoteReserves: BN,
): { quoteAmountOutWithoutLpFee: BN; userQuoteAmountOut: BN } {
  const quoteAmountOutWithoutLpFee = quoteAmountOut.sub(fees.lpFee);
  if (realQuoteReserves.lt(quoteAmountOutWithoutLpFee)) {
    throw new Error(
      "Insufficient real quote reserves to cover the sell output.",
    );
  }
  return {
    quoteAmountOutWithoutLpFee,
    userQuoteAmountOut: quoteAmountOutWithoutLpFee
      .sub(fees.coinCreatorFee)
      .sub(fees.protocolFee),
  };
}

const MAX_FEE_BASIS_POINTS = new BN(10_000); // Assuming MAX_FEE_BASIS_POINTS is 10,000 (100%)

function calculateQuoteAmountOut(
  userQuoteAmountOut: BN,
  lpFeeBasisPoints: BN,
  protocolFeeBasisPoints: BN,
  coinCreatorFeeBasisPoints: BN,
): BN {
  // Calculate the total fee basis points
  const totalFeeBasisPoints = lpFeeBasisPoints
    .add(protocolFeeBasisPoints)
    .add(coinCreatorFeeBasisPoints);
  // Calculate the denominator
  const denominator = MAX_FEE_BASIS_POINTS.sub(totalFeeBasisPoints);
  // Calculate the quote_amount_out
  return ceilDiv(userQuoteAmountOut.mul(MAX_FEE_BASIS_POINTS), denominator);
}

export function sellQuoteInput({
  quote,
  slippage,
  baseReserve,
  quoteReserve,
  virtualQuoteReserves = new BN(0),
  feeBucketsTotal = new BN(0),
  globalConfig,
  baseMintAccount,
  baseMint,
  coinCreator,
  creator,
  feeConfig,
  quoteMint,
  isMayhemMode,
  creatorFeeBps,
  quoteTransferFee,
}: {
  quote: BN;
  slippage: number; // e.g. 1 => 1% slippage tolerance
  baseReserve: BN;
  quoteReserve: BN;
  virtualQuoteReserves?: BN;
  /**
   * `Pool.protocolFees + Pool.creatorFees`: fees v2 trades left in the quote vault. The program
   * pays sells only from `quoteReserve - feeBucketsTotal` (`real_quote_reserves`). Defaults to 0
   * (no fees accrued).
   */
  feeBucketsTotal?: BN;
  globalConfig: GlobalConfig;
  baseMintAccount: RawMint;
  baseMint: PublicKey;
  coinCreator: PublicKey;
  creator: PublicKey;
  feeConfig: FeeConfig | null;
  /**
   * `Pool.quoteMint`; selects the fee schedule (SOL-like -> feeTiers, USDC -> stableFeeTiers,
   * anything else -> exoticFlatFees, or flatFees while the exotic schedule is unset). Defaults to
   * WSOL: omitting it on a non-SOL pool prices with the SOL schedule.
   */
  quoteMint?: PublicKey;
  /** `Pool.isMayhemMode`; defaults to false. */
  isMayhemMode?: boolean;
  /**
   * `Pool.creatorFeeBps`; replaces the schedule's creator rate while
   * `globalConfig.creatorFeeConfigurable` is on and it is nonzero. Omitting it (or 0) prices with
   * the schedule, as before.
   */
  creatorFeeBps?: BN;
  /**
   * The quote mint's Token-2022 transfer fee this epoch (`SwapSolanaState.quoteTransferFee`).
   * `quote` is what should land in the wallet once the fee is withheld from the payout.
   */
  quoteTransferFee?: QuoteTransferFee | null;
}): SellQuoteInputResult {
  // -----------------------------------------
  // 1) Basic validations
  // -----------------------------------------
  if (baseReserve.isZero() || quoteReserve.isZero()) {
    throw new Error(
      "Invalid input: 'baseReserve' or 'quoteReserve' cannot be zero.",
    );
  }

  const effectiveQuoteReserve = quoteReserve.add(virtualQuoteReserves);

  // -----------------------------------------
  // 2) Calculate the fees included in the quote
  // -----------------------------------------
  const {
    lpFeeBps,
    protocolFeeBps,
    creatorFeeBps: coinCreatorFeeBps,
  } = computeFeesBps({
    globalConfig,
    feeConfig,
    creator,
    baseMintSupply: new BN(baseMintAccount.supply.toString()),
    baseMint,
    baseReserve,
    quoteReserve: effectiveQuoteReserve,
    quoteMint,
    isMayhemMode,
    creatorFeeBps,
  });

  // The payout that lands `quote` once the transfer fee is withheld from it.
  const rawQuote = calculateQuoteAmountOut(
    grossForTransferFee(quoteTransferFee, quote),
    lpFeeBps,
    protocolFeeBps,
    PublicKey.default.equals(coinCreator) ? new BN(0) : coinCreatorFeeBps,
  );

  // -----------------------------------------
  // 3) Calculate the base amount needed for the raw quote output
  //    Invert the constant product formula:
  //    base_amount_in = ceil((baseReserve * rawQuote) / (quoteReserve - rawQuote))
  // -----------------------------------------
  if (rawQuote.gte(effectiveQuoteReserve)) {
    throw new Error(
      "Invalid input: Desired quote amount exceeds available reserve.",
    );
  }

  const baseAmountIn = ceilDiv(
    baseReserve.mul(rawQuote),
    effectiveQuoteReserve.sub(rawQuote),
  );

  // Same check as sellBaseInput on the sell this produces: the program covers the gross outflow
  // (user quote plus protocol and creator fees) from real reserves, not just the user's quote.
  const quoteAmountOut = effectiveQuoteReserve
    .mul(baseAmountIn)
    .div(baseReserve.add(baseAmountIn));
  if (
    quoteReserve
      .sub(feeBucketsTotal)
      .lt(quoteAmountOut.sub(fee(quoteAmountOut, lpFeeBps)))
  ) {
    throw new Error(
      "Insufficient real quote reserves to cover the sell output.",
    );
  }

  // -----------------------------------------
  // 4) Calculate minQuote with slippage
  //    - If slippage=1 => 1%, we allow receiving as low as 99% of the desired quote
  // -----------------------------------------
  const minQuote = minAfterSlippage(quote, slippage);

  return {
    internalRawQuote: rawQuote,
    base: baseAmountIn, // amount of base tokens required to get the desired quote
    minQuote, // minimum acceptable tokens after applying slippage
  };
}
