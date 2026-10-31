#!/bin/bash
# rec.sh <trial> <status> <hypothesis> <note> [ratio bytes]
W=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a27-cto-jtbb75hop
K=0x22a10-w15-9120883-jtbb75hop-$1-v1
python3 $W/reconstruction/pump-main/log_attempt.py record --lane w15a27-cto-jtbb75hop --approach jtbb75hop --target 0x22a10 --dedupe-key $K --hypothesis "$3" --status $2 --data "{\"output\":\"$HOME/.cache/pumpfun-reconstruction/lanes/w15a27-cto-jtbb75hop/rx/$1\",\"normalized\":null,\"raw\":null,\"losses\":[],\"raw_losses\":[],\"target\":{\"ratio\":${5:-0},\"slots_diff\":null,\"cand_bytes\":${6:-0}},\"notes\":\"$4\"}" | tail -1
