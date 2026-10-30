# Restore the current Pump corpus's missing multi-hop suite

The maintained 44-suite catalog still requires `multi_hop_curve_partial` (56
cases), but points to a deleted `repro/` harness. Both current aggregate drivers
therefore fail before they can execute that suite. Restore the original bounded
fixture and VM logic under this research directory, retain its historical Git
blob/source attribution, and update the shared catalog and the two drivers'
repository-relative path handling. Existing script basenames and historical
`repro/` paths retain their interpretation.

The restored harness preserves all 56 original synthetic inputs, genuine AMM CPI
signer execution, fresh VMs and original/candidate state/event comparisons. The
sole logic addition propagates its existing failed-case count as a nonzero CLI
status. The captured AMM, Pump and dependency binaries remain untouched. This
does not expand the historical partial recovery lane or import a historical
candidate/expected result as current evidence.

`python -B research/pump-multi-hop-corpus/reproduce.py` actually builds current
Pump, selects this suite from the maintained catalog, and executes it. It then
passes the unchanged captured Mayhem ELF as an explicitly wrong-program negative
input and requires actual differential failures and a nonzero exit. No compiler,
VM or process result is simulated. Actual build inputs, raw ELF hashes, logs and
all case outputs are retained in `work/scoped-proof`.

The 56 cases are partial native/legacy curves only: the historical suite documents
50 cases reaching Pump, six stopping in AMM and 11 successful original outcomes.
They do not establish full source/byte identity, Token-2022/holder/multi-curve
support, security acceptance, or completion of the other 43 suites. Those suites'
separate missing inputs and limitations remain separate.
