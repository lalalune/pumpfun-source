# Running retained census tools

The scripts resolve harness imports relative to their checkout. Supply `--cand` explicitly to census.py, callid_audit.py and dataref_audit.py; no contributor-specific baseline is selected. The existing harness's SDK discovery requirements still apply.

For a different source layout, pass `census.py --pairs pairs.json`, where the JSON object maps original addresses to candidate symbol regexes, for example `{"0x14f4e0":"buy_exact_sol_in$"}`. This replaces the historical pairing map for that run. Duplicate addresses, invalid regexes, missing original windows and unmatched symbols fail rather than silently dropping a pair. Without --pairs the historical map remains available. --only limits reported targets, not identity refinement.

Example: `python reconstruction/pump-main/lanes/callgraph-census/census.py --cand /tmp/pump-out/unstripped.so --pairs /tmp/pairs.json --json /tmp/census.json`.

These reports remain diagnostics, not scoring acceptance or runtime-equivalence evidence. Existing archived census packets are unchanged.
