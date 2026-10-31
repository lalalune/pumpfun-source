#!/usr/bin/env python3
"""Compare two recovered error messages using normally signed offline fixtures."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse
import hashlib
import json
import pathlib
import re

import fees_config_differential as configuration
import fees_sharing_update_differential as sharing
from pump_amm_reusable_harness import pin_program
from pump_differential_output import PumpReport

ROOT = pathlib.Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "evidence/original/pump_fees/deployed.so"
ERROR = re.compile(r"Error Code: (.*?)\. Error Number: (\d+)\. Error Message: (.*)$")


def error_messages(result):
    return [list(match.groups()) for line in result["logs"] if (match := ERROR.search(line))]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=pathlib.Path, required=True)
    parser.add_argument("--baseline", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    publisher = PumpReport(args.output, ROOT, args.candidate, __file__, extra_inputs=[args.baseline] if args.baseline else ())
    original_image = pin_program(ORIGINAL)
    candidate = pin_program(args.candidate)
    baseline = pin_program(args.baseline) if args.baseline else None
    rows = []
    specifications = [
        ("configuration", configuration, "update_fee_config-count-51", "6003",
         ["error", "data_hex", "lamports", "owner", "balance_deltas", "events", "inner_instructions"]),
        ("sharing", sharing, "new-count-11", "6011",
         ["error", "before", "after", "events", "inner", "return"]),
    ]
    for family, module, suffix, code, fields in specifications:
        case = next(case for case in module.cases() if case["name"].endswith(suffix))

        def run(binary):
            return module.ConfigFixture(binary).run(case) if family == "configuration" else module.run(case, binary)

        original, candidate_result = run(original_image), run(candidate)
        messages = error_messages(original)
        if not (len(messages) == 1 and messages[0][1:] == [code, "format."]):
            raise ValueError(f"original {family} case did not emit error {code}: {messages}")
        matched = all(original[key] == candidate_result[key] for key in fields)
        matched = matched and messages == error_messages(candidate_result)
        row = {"case": case, "original": original, "candidate": candidate_result,
               "compared_fields": fields, "original_error_messages": messages,
               "candidate_error_messages": error_messages(candidate_result), "match": matched}
        if baseline:
            row["baseline"] = run(baseline)
            row["baseline_error_messages"] = error_messages(row["baseline"])
        rows.append(row)
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    report = {
        "scope": "Two normally signed offline synthetic cases compare error name/number/message, state, balances, events and inner calls. Source-location and compute-log differences are retained but excluded from the message comparison. No full source or executable equality claim.",
        "original_sha256": sha(original_image), "candidate_sha256": sha(candidate),
        "case_count": len(rows), "cases": rows,
        "mismatches": [row["case"]["name"] for row in rows if not row["match"]],
    }
    if baseline:
        report["baseline_sha256"] = sha(baseline)
    publisher.write((json.dumps(report, indent=2) + "\n").encode('utf-8'))
    print(json.dumps({"cases": len(rows), "mismatches": report["mismatches"]}))
    if report["mismatches"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
