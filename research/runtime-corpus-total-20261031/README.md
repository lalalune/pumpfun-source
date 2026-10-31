# Derive the serial Pump corpus total from its suite catalogue

Base: `90300f9d2efe3ef014b116172251a41bfb104d78`. Observed 2026-10-31.

Commit `d811fd0e2341f219eeebcc90f1a5b6b28f0653e2` increased the Admin CTO suite from 363 to 388 cases. The 44 declared suite counts now sum to **10,493**, but the serial validator still required **10,468** after accepting every suite. Each preceding per-suite check requires the corresponding catalogue value, and every suite is included in the final sum. Those conditions therefore contradict the old final constant.

The final check now derives its expected total from `EXPECTED_CASES`. Existing serial publication tests now use the actual catalogue counts instead of synthetic counts chosen to total 10,468. Their producers remain mocked publication fixtures: the focused test fails at the actual final assertion on the base and passes after the fix; the complete ten-test retention suite passes.

Independent runtime evidence comprises **43 real original-vs-original producers and 10,473 cases**: all 41 generic producers (9,910 cases), QuoteControl (507), and partial multi-hop (56). The remaining two-curve suite requires a genuine matching SBF compiler receipt, unavailable in this session, so its 20 cases were not executed and no receipt was fabricated. The full 44-suite serial CLI is not claimed.

The narrow reproduction executes the actual final assertion extracted from `main` against the authoritative catalogue, without running a compiler or substituting its expression. The valid catalogue fails before and passes after; missing-suite and wrong-count controls fail both times:

```sh
python research/runtime-corpus-total-20261031/reproduce.py --repo /path/to/checkout --output /tmp/fresh-total-proof.json
python -B scripts/test_pump_validate_all_retention.py
```

`results.json` separates the isolated-guard proof, real producer runs, and mocked publication test. All 9 retained captures verify and all 242 tooling tests pass. No capture, compiled program, historical packet or per-suite expected count changed.
