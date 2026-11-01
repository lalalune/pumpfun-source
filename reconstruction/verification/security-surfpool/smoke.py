#!/usr/bin/env python3
"""Smoke-test original Pump initialization through offline Surfpool."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "scripts"))
import pump_global_init_differential as fixture
from surfpool_rpc import Surfpool, RecordingVM, original, install_fixture, resign

out = HERE / "results/smoke"
recorded = []
def factory():
    vm = RecordingVM()
    recorded.append(vm)
    return vm

original_type = fixture.LiteSVM
fixture.LiteSVM = factory
try:
    lite = fixture.run({"name": "base"})
finally:
    fixture.LiteSVM = original_type
vm = recorded[0]
with Surfpool(out, binary=HERE / "tools/surfpool") as pool:
    pool.load_program(fixture.P, original("pump"))
    install_fixture(pool, vm)
    tx = resign(vm.transaction, fixture.PAYER.pubkey(), [fixture.PAYER, fixture.USER],
                pool.latest_blockhash())
    result = pool.send(tx)
    result["loaded_programs"] = pool.loaded_programs
    result["litesvm_error"] = lite["error"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"surfpool_error": result["error"],
                      "litesvm_error": lite["error"],
                      "programs": result["loaded_programs"]}, indent=2))
    assert result["error"] is None
