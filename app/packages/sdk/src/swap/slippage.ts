import BN from "bn.js";

const PRECISION = new BN(1_000_000_000);

/**
 * Slippage is a percent. A negative value inverts the bound, and a value
 * above 100 makes a sell minimum negative before it is encoded.
 */
export function assertSlippagePercent(slippage: number): void {
  if (!Number.isFinite(slippage) || slippage < 0 || slippage > 100) {
    throw new Error("Slippage must be between 0 and 100 (0% to 100%)");
  }
}

/** `amount * (1 + slippage/100)`, rounded down at 1e-9. */
export function maxAfterSlippage(amount: BN, slippage: number): BN {
  assertSlippagePercent(slippage);
  const factor = new BN(Math.floor((1 + slippage / 100) * 1_000_000_000));
  return amount.mul(factor).div(PRECISION);
}

/** `amount * (1 - slippage/100)`, rounded down at 1e-9. */
export function minAfterSlippage(amount: BN, slippage: number): BN {
  assertSlippagePercent(slippage);
  const factor = new BN(Math.floor((1 - slippage / 100) * 1_000_000_000));
  return amount.mul(factor).div(PRECISION);
}
