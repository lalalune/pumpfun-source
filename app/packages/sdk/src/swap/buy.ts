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
  BuyBaseInputResult,
  BuyQuoteInputResult,
  FeeConfig,
  GlobalConfig,
} from "./types";
import { maxAfterSlippage } from "./slippage";
import { ceilDiv, fee } from "./util";

/**
 * Everything that leaves the buyer's account for a buy the pool books at
 * `quoteAmountIn + lpFee + protocolFee + coinCreatorFee`, the quote's Token-2022 transfer fee
 * included (nothing more on an untaxed quote). What goes to the vault is grossed up so the pool
 * books exactly its share once the fee is withheld; what goes to a fee recipient is sent as it is.
 * The v1 `buy` sends the vault `quoteAmountIn + lpFee`; a v2 trade sends it everything but the
 * buyback slice of the protocol fee (floor of `buybackBasisPoints`; none on a mayhem pool).
 *
 * rust reference: pump-amm buy() `vault_gross`, trade_v2 BuyLeg::user_debit()
 */
export function buyDebit({
  quoteAmountIn,
  lpFee,
  protocolFee,
  coinCreatorFee,
  quoteTransferFee,
  tradeV2 = false,
  globalConfig,
  isMayhemMode = false,
}: {
  quoteAmountIn: BN;
  lpFee: BN;
  protocolFee: BN;
  coinCreatorFee: BN;
  quoteTransferFee?: QuoteTransferFee | null;
  tradeV2?: boolean;
  globalConfig: GlobalConfig;
  isMayhemMode?: boolean;
}): BN {
  const booked = quoteAmountIn.add(lpFee).add(protocolFee).add(coinCreatorFee);
  const buybackFee =
    tradeV2 && !isMayhemMode
      ? protocolFee.mul(globalConfig.buybackBasisPoints).divn(10_000)
      : new BN(0);
  const vault = tradeV2 ? booked.sub(buybackFee) : quoteAmountIn.add(lpFee);
  return booked.add(grossForTransferFee(quoteTransferFee, vault).sub(vault));
}

/**
 * The exact-quote-in fee split of a v2 buy: the net that prices the swap, floor-divided out of
 * `spendableQuoteIn` and shaved until net + fees fits the budget, and the fees, ceil-computed on
 * the net *before* the shave (the program keeps them; the caller decides what the shave funds).
 * A zero creator rate charges nothing, as on a pool without a coin creator.
 *
 * rust reference: pump-amm trade_v2 exact_quote_in_fees()
 */
export function exactQuoteInFees(
  spendableQuoteIn: BN,
  {
    lpFeeBps,
    protocolFeeBps,
    creatorFeeBps,
  }: { lpFeeBps: BN; protocolFeeBps: BN; creatorFeeBps: BN },
): { netQuoteForSwap: BN; lpFee: BN; protocolFee: BN; coinCreatorFee: BN } {
  const totalFeeBps = lpFeeBps.add(protocolFeeBps).add(creatorFeeBps);
  let netQuoteForSwap = spendableQuoteIn
    .muln(10_000)
    .div(totalFeeBps.addn(10_000));
  if (netQuoteForSwap.lten(0)) {
    throw new Error("The quote budget does not cover the fees.");
  }
  const lpFee = fee(netQuoteForSwap, lpFeeBps);
  const protocolFee = fee(netQuoteForSwap, protocolFeeBps);
  const coinCreatorFee = fee(netQuoteForSwap, creatorFeeBps);
  const excess = netQuoteForSwap
    .add(lpFee)
    .add(protocolFee)
    .add(coinCreatorFee)
    .sub(spendableQuoteIn);
  if (excess.gtn(0)) {
    netQuoteForSwap = netQuoteForSwap.sub(excess);
    if (netQuoteForSwap.lten(0)) {
      throw new Error("The quote budget does not cover the fees.");
    }
  }
  return { netQuoteForSwap, lpFee, protocolFee, coinCreatorFee };
}

export function buyBaseInput({
  base,
  slippage,
  baseReserve,
  quoteReserve,
  virtualQuoteReserves = new BN(0),
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
  tradeV2,
}: {
  base: BN;
  slippage: number; // 1 => 1%
  baseReserve: BN;
  quoteReserve: BN;
  virtualQuoteReserves?: BN;
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
   * The quote mint's Token-2022 transfer fee this epoch (`SwapSolanaState.quoteTransferFee`);
   * omitting it on a taxed quote under-prices the debit. `uiQuote` and `maxQuote` include it.
   */
  quoteTransferFee?: QuoteTransferFee | null;
  /** Price the debit as `buy_v2` charges it (the buyback slice is not grossed up); v1 by default. */
  tradeV2?: boolean;
}): BuyBaseInputResult {
  // -----------------------------------------------------
  // 1) Basic validations
  // -----------------------------------------------------
  if (baseReserve.isZero() || quoteReserve.isZero()) {
    throw new Error(
      "Invalid input: 'baseReserve' or 'quoteReserve' cannot be zero.",
    );
  }
  if (base.gt(baseReserve)) {
    throw new Error("Cannot buy more base tokens than the pool reserves.");
  }

  // -----------------------------------------------------
  // 2) Calculate the raw quote needed (Raydium-like formula)
  //    quote_amount_in = ceil_div(quote_reserve * base, base_reserve - base)
  // -----------------------------------------------------
  const effectiveQuoteReserve = quoteReserve.add(virtualQuoteReserves);

  const numerator = effectiveQuoteReserve.mul(base);
  const denominator = baseReserve.sub(base);

  if (denominator.isZero()) {
    throw new Error("Pool would be depleted; denominator is zero.");
  }

  const quoteAmountIn = ceilDiv(numerator, denominator);

  // -----------------------------------------------------
  // 3) Calculate fees
  //    - LP Fee = floor((quoteAmountIn * lpFeeBps) / 10000)
  //    - Protocol Fee = floor((quoteAmountIn * protocolFeeBps) / 10000)
  // -----------------------------------------------------
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

  const lpFee = fee(quoteAmountIn, lpFeeBps);
  const protocolFee = fee(quoteAmountIn, protocolFeeBps);
  const coinCreatorFee = PublicKey.default.equals(coinCreator)
    ? new BN(0)
    : fee(quoteAmountIn, coinCreatorFeeBps);

  const totalQuote = buyDebit({
    quoteAmountIn,
    lpFee,
    protocolFee,
    coinCreatorFee,
    quoteTransferFee,
    tradeV2,
    globalConfig,
    isMayhemMode,
  });

  // -----------------------------------------------------
  // 4) Calculate maxQuote with slippage
  //    If slippage=1 => factor = (1 + 1/100) = 1.01
  // -----------------------------------------------------
  const maxQuote = maxAfterSlippage(totalQuote, slippage);

  return {
    internalQuoteAmount: quoteAmountIn,
    uiQuote: totalQuote, // Final total quote after fees
    maxQuote,
  };
}

export function buyQuoteInput({
  quote,
  slippage,
  baseReserve,
  quoteReserve,
  virtualQuoteReserves = new BN(0),
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
  tradeV2,
}: {
  quote: BN;
  slippage: number; // 1 => 1%
  baseReserve: BN;
  quoteReserve: BN;
  virtualQuoteReserves?: BN;
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
   * `quote` is what leaves the wallet, the fee included, as the program's exact-in budget is.
   */
  quoteTransferFee?: QuoteTransferFee | null;
  /** Fit the debit as `buy_exact_quote_in_v2` does (the buyback slice is not grossed up). */
  tradeV2?: boolean;
}): BuyQuoteInputResult {
  // -----------------------------------------------------
  // 1) Basic validations
  // -----------------------------------------------------
  if (baseReserve.isZero() || quoteReserve.isZero()) {
    throw new Error(
      "Invalid input: 'baseReserve' or 'quoteReserve' cannot be zero.",
    );
  }

  const effectiveQuoteReserve = quoteReserve.add(virtualQuoteReserves);

  // -----------------------------------------------------
  // 2) Calculate fees total fee basis points and denominator
  // -----------------------------------------------------
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

  const totalFeeBps = lpFeeBps
    .add(protocolFeeBps)
    .add(PublicKey.default.equals(coinCreator) ? new BN(0) : coinCreatorFeeBps);
  const denominator = new BN(10_000).add(totalFeeBps);
  // -----------------------------------------------------
  // 3) Calculate effective quote amount: the derivation runs on what the budget lands once the
  //    quote's transfer fee is withheld, then the actual debit is fitted to the budget.
  // -----------------------------------------------------
  const spendable = netOfTransferFee(quoteTransferFee, quote);
  if (spendable.lten(0)) {
    throw new Error("The quote budget does not cover the transfer fee.");
  }
  let effectiveQuote = spendable.mul(new BN(10_000)).div(denominator);

  const lpFee = fee(effectiveQuote, lpFeeBps);
  const protocolFee = fee(effectiveQuote, protocolFeeBps);
  const coinCreatorFee = PublicKey.default.equals(coinCreator)
    ? new BN(0)
    : fee(effectiveQuote, coinCreatorFeeBps);
  const totalWithFees = effectiveQuote
    .add(lpFee)
    .add(protocolFee)
    .add(coinCreatorFee);
  if (totalWithFees.gt(spendable)) {
    effectiveQuote = effectiveQuote.sub(totalWithFees.sub(spendable));
  }
  const debit = buyDebit({
    quoteAmountIn: effectiveQuote,
    lpFee,
    protocolFee,
    coinCreatorFee,
    quoteTransferFee,
    tradeV2,
    globalConfig,
    isMayhemMode,
  });
  if (debit.gt(quote)) {
    effectiveQuote = effectiveQuote.sub(debit.sub(quote));
  }
  if (effectiveQuote.lten(0)) {
    throw new Error("The quote budget does not cover the fees.");
  }

  // -----------------------------------------------------
  // 4) Calculate the base tokens received using effectiveQuote
  //    base_amount_out = floor(base_reserve * effectiveQuote / (quote_reserve + effectiveQuote))
  // -----------------------------------------------------
  const inputAmount = effectiveQuote.subn(1);
  const numerator = baseReserve.mul(inputAmount);
  const denominatorEffective = effectiveQuoteReserve.add(inputAmount);

  if (denominatorEffective.isZero()) {
    throw new Error("Pool would be depleted; denominator is zero.");
  }

  const baseAmountOut = numerator.div(denominatorEffective);

  // -----------------------------------------------------
  // 5) Calculate maxQuote with slippage
  //    If slippage=1 => factor = (1 + 1/100) = 1.01
  // -----------------------------------------------------
  const maxQuote = maxAfterSlippage(quote, slippage);

  return {
    base: baseAmountOut, // Base tokens received after fees
    internalQuoteWithoutFees: effectiveQuote,
    maxQuote, // Maximum quote tokens to pay (with slippage)
  };
}
