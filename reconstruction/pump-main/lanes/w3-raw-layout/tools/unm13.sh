#!/bin/bash
H=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction/harness
SO=$1
for p in "0x1e7c0 9create_v27execute" "0x22a10 9admin_cto7execute" "0x4c158 create_token_account_v2" "0x5b3b0 15multi_hop_curve8swap_hop17h" "0x72810 5sweep7execute" "0x80df8 v3_buy_costs" "0x83c00 v3_execute_buy17" "0x13b9b8 buy_handler17" "0x13f630 buy_exact_quote_in_handler17" "0x144508 14pump_recovered14pump_recovered7sell_v217h" "0x147ba0 5trade3buy17" "0x1489f8 5trade15buy_exact_quote17" "0x14a8a8 5trade4sell17"; do set -- $p; python3 $H/target_metric.py $SO $1 --sym "$2" 2>/dev/null | python3 -c "import sys,json;d=json.loads(sys.stdin.read().strip().split('\n')[-1]);print(d['window'],d['ratio'],d['cand_bytes'])"; done
