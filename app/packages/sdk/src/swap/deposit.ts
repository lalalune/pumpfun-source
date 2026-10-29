import BN from "bn.js";

import { maxAfterSlippage } from "./slippage";
import { grossForTransferFee, QuoteTransferFee } from "./transferFee";
import { DepositLpTokenResult, DepositResult } from "./types";

export function depositToken0(
  token0: BN,
  slippage: number,
  token0Reserve: BN,
  token1Reserve: BN,
  totalLpTokens: BN,
): DepositResult {
  // Calculate the corresponding output amount based on the pool's reserves
  const token1 = token0.mul(token1Reserve).div(token0Reserve);

  const maxToken0 = maxAfterSlippage(token0, slippage);
  const maxToken1 = maxAfterSlippage(token1, slippage);

  // Calculate the LP tokens to mint, proportional to the deposit amount
  const lpToken = token0.mul(totalLpTokens).div(token0Reserve);

  return {
    token1,
    lpToken,
    maxToken0,
    maxToken1,
  };
}

function ceilDiv(numerator: BN, denominator: BN): BN {
  return numerator.add(denominator).sub(new BN(1)).div(denominator);
}

export function depositLpToken(
  lpToken: BN,
  slippage: number,
  baseReserve: BN,
  quoteReserve: BN,
  totalLpTokens: BN,
  /**
   * The quote mint's Token-2022 transfer fee (`LiquiditySolanaState.quoteTransferFee`): the
   * deposit is grossed up so the pool receives its share, and `maxQuote` caps that debit.
   */
  quoteTransferFee?: QuoteTransferFee | null,
): DepositLpTokenResult {
  if (totalLpTokens.isZero()) {
    throw new Error("Division by zero: totalLpTokens cannot be zero");
  }

  const baseAmountIn = ceilDiv(baseReserve.mul(lpToken), totalLpTokens);
  const quoteAmountIn = grossForTransferFee(
    quoteTransferFee,
    ceilDiv(quoteReserve.mul(lpToken), totalLpTokens),
  );

  const maxBase = maxAfterSlippage(baseAmountIn, slippage);
  const maxQuote = maxAfterSlippage(quoteAmountIn, slippage);

  return {
    maxBase,
    maxQuote,
  };
}
