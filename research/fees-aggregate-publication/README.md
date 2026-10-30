# Preserve Fees aggregate inputs during report publication

At base `1043a51e8798c5974a84ecaed5c85e9d6938cfce`, the Fees aggregate
pins its candidate ELF, executes all 18 real differential suites, then writes
JSON directly to the caller's output. If output aliases the selected ELF,
the snapshot keeps execution successful while the original caller's ELF is
overwritten. Other evidence/code inputs and earlier report bytes also lack
the existing shared report writer's admission and atomic staging.

Reuse `PumpReport`, already used by differential runners, with the original
candidate path before snapshotting and the Fees evidence, suite code,
source and retained query inputs. It checks path/symlink/hardlink aliases
before execution and again before publication, then atomically publishes
complete report bytes. Ordinary report replacement remains supported.
The 18 suite commands, synthetic transactions, case generators, comparisons
and program bytes are unchanged.

## Real proof

With Python 3.12 and pinned `requirements.txt` on a LiteSVM-capable host:

```sh
python -B research/fees-aggregate-publication/reproduce.py
python -B scripts/verify_evidence.py
python -B scripts/test_tooling.py
```

The same proof first runs every suite with a disposable copy of the captured
Fees ELF as candidate. This original/original control validates publication
behavior, not reconstruction gains. It then repeats the actual aggregate
CLI with that copied ELF as output. Before, the aggregate exits zero and
destroys its caller's ELF; after, admission rejects the alias and preserves
the bytes before any suite starts. It finally checks that an ordinary prior
report can be replaced after a second complete 18-suite execution.

Only disposable copies are used for destructive before reproduction. The
canonical capture is hashed before and after and never modified. Logs,
complete compressed reports and observed return codes are retained under
`work/scoped-proof`. No fabricated child report or mocked VM is used.

This fixes report/input preservation in on-chain differential tooling. It
does not rebuild Fees, establish new handler coverage or claim security or
byte identity for reconstructed source. Historical evidence is retained;
the accompanying asset transition proposes only this aggregate script hash.
