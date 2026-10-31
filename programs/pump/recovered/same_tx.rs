//! Captured outcome of one transaction holding several instructions, Pump
//! calls among them, next to the same instructions sent one transaction each.
//!
//! The steps come in as measured alone, in order, on one chain of state: what
//! each returned, the compute units it took and how many entries it added to
//! the instruction trace. Pricing stays with the instruction models. This
//! module holds what the transaction adds on top: one fee, one all-or-nothing
//! end state, one compute budget and one trace of 64 entries.
//!
//! Each Pump call reads what the call before it stored, in the same way as if
//! a new transaction sat between them: a closed `user_volume_accumulator` can
//! be reopened by the next instruction, and a buy, a sell, `create` or
//! `migrate` need no slot boundary.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_same_tx_captured.py`. Not linked into the SBF crate. This is not
//! a byte-identity claim.
//!
//! Unconfirmed (outside the checked inputs): the default budget, which no case
//! here exceeds, and the order of a budget and a trace failure inside one step.

/// Lamports per signature.
pub const SIGNATURE_FEE: u64 = 5_000;
/// Top-level instructions and CPIs together.
pub const MAX_TRACE: u64 = 64;
/// `SetComputeUnitLimit` costs this much, and so does a system transfer.
pub const BUDGET_INSTRUCTION_UNITS: u64 = 150;
/// Beside `create`, each later step that lists the mint takes this much less
/// than it does alone. The cause is 미확인; the mint signs that transaction.
pub const SIGNED_MINT_SAVING: u64 = 3;
/// 미확인: no case reaches these three.
pub const DEFAULT_PROGRAM_UNITS: u64 = 200_000;
pub const DEFAULT_BUILTIN_UNITS: u64 = 3_000;
pub const MAX_UNITS: u64 = 1_400_000;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Step {
    /// `None` when the step succeeded alone, else the label of its failure.
    pub failure: Option<String>,
    pub units: u64,
    pub trace: u64,
    /// Signatures the step needs when it is alone in a transaction.
    pub signatures: u64,
    /// A system transfer, not a Pump call.
    pub builtin: bool,
    /// The step lists the mint among its accounts.
    pub names_mint: bool,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Outcome {
    /// Every step ran. `saved` is what the single fee saves against one
    /// transaction per step, so the end state is the separate runs' end state
    /// plus `saved` lamports to the payer.
    Passed { fee: u64, saved: u64, units: u64, trace: u64 },
    /// Nothing but the fee leaves the state before the transaction.
    Failed { index: u64, failure: String, fee: u64 },
}

fn default_limit(steps: &[Step]) -> u64 {
    let builtin = steps.iter().filter(|s| s.builtin).count() as u64;
    let programs = steps.len() as u64 - builtin;
    (programs * DEFAULT_PROGRAM_UNITS + builtin * DEFAULT_BUILTIN_UNITS).min(MAX_UNITS)
}

/// `limit` is the value of a leading `SetComputeUnitLimit`, which takes index 0.
/// `signatures` counts the whole transaction, steps that never ran included.
pub fn run(steps: &[Step], limit: Option<u64>, signatures: u64) -> Outcome {
    let fee = signatures * SIGNATURE_FEE;
    let lead = u64::from(limit.is_some());
    let budget = limit.unwrap_or_else(|| default_limit(steps));
    let mut units = lead * BUDGET_INSTRUCTION_UNITS;
    let mut trace = lead;
    for (position, step) in steps.iter().enumerate() {
        let index = position as u64 + lead;
        trace += step.trace;
        if trace > MAX_TRACE {
            return Outcome::Failed { index, failure: "trace".to_string(), fee };
        }
        units += step.units;
        if step.names_mint && signatures == 2 {
            units -= SIGNED_MINT_SAVING;
        }
        if units > budget {
            return Outcome::Failed { index, failure: "budget".to_string(), fee };
        }
        if let Some(failure) = &step.failure {
            return Outcome::Failed { index, failure: failure.clone(), fee };
        }
    }
    let alone: u64 = steps.iter().map(|s| s.signatures * SIGNATURE_FEE).sum();
    Outcome::Passed { fee, saved: alone - fee, units, trace }
}
