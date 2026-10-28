# coordbodyA-01 (base L06, identity recipe): 900 normalized / 165 raw (+1: 0x3dd78)

## Change
`src/fee_recipient.rs` `validate_fee_recipient`: mayhem branch first, early-return form, both errors on the
original lines (fee_recipient.rs:19 mayhem / :35 normal):

    if bonding_curve.is_mayhem_mode {
        if key == global.reserved_fee_recipient || global.reserved_fee_recipients.contains(&key) { return Ok(()); }
        return err!(PumpError::NotAuthorized);          // line 19
    }
    if key == global.fee_recipient || global.fee_recipients.binary_search(&key).is_ok() { return Ok(()); }
    err!(PumpError::NotAuthorized)                      // line 35

## Binary evidence
- Original 0x3dd78 (2008 B) records two NotAuthorized (6000) Source sites: line 0x23=35 in the binary-search
  (non-mayhem) failure block, line 0x13=19 in the reserved-recipient (mayhem) failure block (the harness'
  coords.py reports "35,35" because it re-reads the first line slot; the second stw imm at 0x3e4d0 is 0x13).
- The early-return shape is what places the shared return block after both error blocks (error 1 `ja` over
  error 2, error 2 falls into the return) and gives the ret-ptr spill -0x160 / Ok-tag spill -0x168 order.
  if/else (base, fr2), match (fr4), require! (fr1, fr5) forms all keep the base layout; fr3 is byte-identical
  (normalized) to the original.
- Behaviour unchanged: same predicates, same error, same order of evaluation; the function now matches the
  original by construction.
- Line-neutral: fee_recipient.rs has no other Source sites (its other original window 0x3e550 is not
  reconstructed in L06); the file shrinks by 8 lines at the end. No losses.
