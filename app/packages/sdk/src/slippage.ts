import BN from "bn.js";

/**
 * `amount` less `slippage` percent, never below `floor`.
 *
 * A buy's `min_tokens_out` uses floor 1. A sell's minimum may be 0.
 * Slippage outside 0..100 is rejected: a negative percent increases the
 * minimum above `amount`, and a percent above 100 makes the subtraction
 * negative before the floor.
 */
export function lessSlippage(amount: BN, slippage: number, floor = 0): BN {
  if (!Number.isFinite(slippage) || slippage < 0 || slippage > 100) {
    throw new RangeError(
      `slippage percent must be finite and between 0 and 100, got ${String(slippage)}`,
    );
  }
  const withheld = amount
    .mul(new BN(Math.floor(slippage * 10)))
    .div(new BN(1000));
  return BN.max(amount.sub(withheld), new BN(floor));
}
