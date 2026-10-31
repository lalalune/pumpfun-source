//! Captured outcome of one transaction holding several trade instructions
//! (`buy_v2`, `sell_v2`, `buy_exact_quote_in_v2`, `buy_v3`, `sell_v3`,
//! `buy_exact_quote_in_v3`), next to the same instructions sent one
//! transaction each.
//!
//! `same_tx.rs` folds measured steps of the legacy instructions into one
//! transaction's outcome and leaves two things unconfirmed: the default
//! budget, which no case there exceeds, and the order of a budget and a
//! trace failure inside one step. This module is the same fold for trade
//! steps, with both points measured by
//! `tests/test_same_tx_trades_captured.py`:
//!
//! - The default budget is one pool for the whole transaction:
//!   200,000 units per program instruction plus 3,000 per builtin
//!   instruction, capped at 1,400,000. It is not a per-instruction cap: a
//!   `buy_v2` step measured at 255,845 units runs inside a two-step pool
//!   of 400,000 and is only stopped in a one-step pool of 200,000. A
//!   transaction of one such step and `k` system transfers fails at
//!   exactly 200,000 + 3,000k units for every `k` up to the flip, and
//!   passes from the first `k` whose pool covers the steps.
//! - Inside one step, the budget and trace crossings are ordered by
//!   where they fall in the step's execution: a step's trace is complete
//!   at `fill` units (for the calibrated `sell_v2` step, 150,922 of its
//!   155,438 units — its last trace entry is a CPI near its end). A
//!   budget that runs out before `fill` reports `budget`; a budget that
//!   lasts to `fill` reports `trace`, even if it would run out in the
//!   step's tail.
//!
//! One fee: 5,000 lamports for the transaction's one signature, whether
//! the transaction passes or fails, against 5,000 per step when the steps
//! run one transaction each. All or nothing: a failure at any step leaves
//! the start state less the fee. Pricing stays with the trade models;
//! this module holds only what the transaction adds on top.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_same_tx_trades_captured.py`. Not linked into the SBF
//! crate. This is not a byte-identity claim.
//!
//! Unconfirmed (outside the checked inputs): the 1,400,000 cap under the
//! default budget — every trade step here fills the 64-entry trace
//! before a default pool can reach the cap, so the cap is only checked
//! under an explicit limit, as in `same_tx.rs` — and compute-budget
//! instructions other than one leading `SetComputeUnitLimit`.

/// Lamports for the transaction's one signature.
pub const SIGNATURE_FEE: u64 = 5_000;
/// Top-level instructions and CPIs together.
pub const MAX_TRACE: u64 = 64;
/// `SetComputeUnitLimit` costs this much, and so does a system transfer.
pub const BUDGET_INSTRUCTION_UNITS: u64 = 150;
/// Default pool per program instruction, measured.
pub const DEFAULT_PROGRAM_UNITS: u64 = 200_000;
/// Default pool per builtin instruction (a system transfer), measured.
pub const DEFAULT_BUILTIN_UNITS: u64 = 3_000;
/// The default pool never exceeds this.
pub const MAX_UNITS: u64 = 1_400_000;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Step {
    /// `None` when the step succeeded alone, else the label of its failure.
    pub failure: Option<String>,
    /// Units the step took alone, on the chain the steps build together.
    pub units: u64,
    /// Trace entries the step added alone: itself plus its CPIs.
    pub trace: u64,
    /// Units the step spends before its last trace entry lands. The test
    /// measures this for the step it pairs with a trace crossing under a
    /// tight budget; for every other step it passes the step's whole
    /// `units`, which only a both-crossing step could tell apart.
    pub fill: u64,
    /// A system transfer, not a program call.
    pub builtin: bool,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Outcome {
    /// Every step ran. `saved` is what the single fee saves against one
    /// transaction per step, so the end state is the separate runs' end
    /// state plus `saved` lamports to the payer.
    Passed { fee: u64, saved: u64, units: u64, trace: u64 },
    /// Nothing but the fee leaves the state before the transaction.
    Failed { index: u64, failure: String, fee: u64 },
}

fn default_limit(steps: &[Step]) -> u64 {
    let builtin = steps.iter().filter(|s| s.builtin).count() as u64;
    let programs = steps.len() as u64 - builtin;
    (programs * DEFAULT_PROGRAM_UNITS + builtin * DEFAULT_BUILTIN_UNITS).min(MAX_UNITS)
}

/// `limit` is the value of a leading `SetComputeUnitLimit`, which takes
/// index 0. The steps are trades from the checked fixtures, so the
/// transaction carries one signature throughout.
pub fn run(steps: &[Step], limit: Option<u64>) -> Outcome {
    let fee = SIGNATURE_FEE;
    let lead = u64::from(limit.is_some());
    let budget = limit.unwrap_or_else(|| default_limit(steps));
    let mut units = lead * BUDGET_INSTRUCTION_UNITS;
    let mut trace = lead;
    for (position, step) in steps.iter().enumerate() {
        let index = position as u64 + lead;
        if trace + step.trace > MAX_TRACE {
            // The trace fills inside this step, at `fill` units into it.
            // A budget that runs out before then is reported instead.
            if budget < units + step.fill {
                return Outcome::Failed { index, failure: "budget".to_string(), fee };
            }
            return Outcome::Failed { index, failure: "trace".to_string(), fee };
        }
        units += step.units;
        if units > budget {
            return Outcome::Failed { index, failure: "budget".to_string(), fee };
        }
        if let Some(failure) = &step.failure {
            return Outcome::Failed { index, failure: failure.clone(), fee };
        }
        trace += step.trace;
    }
    let alone = steps.len() as u64 * SIGNATURE_FEE;
    Outcome::Passed { fee, saved: alone - fee, units, trace }
}
