# Mayhem publication test inputs

These six case lists are exact bytes restored from commit
`b4448f7bc202063a711565b543ae4b49770def90`, before the old `repro/`
workspace was removed. `provenance.json` records original paths, SHA-256 hashes
and case counts. They are synthetic local transaction inputs, not captured
transaction outputs or proof of candidate equivalence.

The publication tests execute each native selection with the captured original
ELF as the comparison input; bounded controls select two real cases. Token quote
family controls are bounded separately. Historical result packets are not
restored, and this fixture alone makes no claim about a rebuilt program.
