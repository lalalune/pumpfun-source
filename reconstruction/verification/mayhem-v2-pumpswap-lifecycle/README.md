# Mayhem V2 and PumpSwap persistent lifecycle differential

## Coverage audit

The merged `mayhem-stateful-lifecycle` package deliberately limits its
persistent trade coverage to legacy native-SOL `buy` and `sell`. The retained
`mayhem_buy_v2_differential.py`, `mayhem_sell_v2_differential.py`, and
`mayhem_pump_swap_differential.py` tools each construct a new LiteSVM for every
case. They prove broad single-transaction admission behavior, but no successful
V2 or PumpSwap trade supplies state to a later transaction.

This package closes that specific gap. It executes authenticated Mayhem V2 and
Mayhem PumpSwap instructions in persistent, independent LiteSVM instances and
records the complete watched state before and after each signed transaction.
It does not duplicate legacy Mayhem coverage and does not change any program
source or reconstruction score.

The fixture is `synthetic_preinitialized`: canonical PDAs and genuine captured
programs are used, but Mayhem initialization is not claimed. Mayhem signs only
for its canonical `sol-vault` PDA during real Pump/PumpSwap CPIs. Ordinary
test-owned Ed25519 keys sign every outer transaction.

## Qualified images

- captured Mayhem allocation: 777,408 bytes, SHA-256
  `a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb`
- exact meaningful-ELF candidate: 775,416 bytes, SHA-256
  `9af9e3b1cbc9d89340af4d9d46e4c88d3dc2fc67e0090f9370047d97532ff09d`

The candidate is the artifact qualified by
`reconstruction/mayhem/native-linux-qualification/QUALIFICATION.json` and the
exact Windows build run recorded in `provenance.json`. No compiler run is
required by this package.

Implementation, qualification results, replay commands, independent verifier
coverage, and limitations are completed in subsequent commits.
