# Batch target diagnostics

Compare multiple original windows against one candidate in a single invocation:

```sh
python3 reconstruction/harness/target_metric.py /tmp/trial/unstripped.so 0x147ba0 0x1489f8 0x14a8a8 --top 3 --json /tmp/trial/targets.json
```

The candidate and original inventory are loaded once. Addresses are processed in
request order, with duplicate addresses coalesced. All requested addresses and
options are validated before candidate analysis or output; an unknown address does
not produce a partial batch. Standard output retains the existing JSON-lines row
format; `--json` additionally saves the same rows as a JSON array.

`--top` applies per window to heuristic selection. As before, explicit `--sym`
selection reports every matching symbol. `--slots 0` retains counts while omitting
the offset details. Ratios and slot distances are diagnostics; the official scorer
and preservation of baseline matches still decide acceptance.
