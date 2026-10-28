#!/bin/bash
# Open a PR that adds one research packet directory.
# usage: pr.sh PACKET_DIR "commit/PR title" BODY_FILE
#   PACKET_DIR's basename becomes research/<basename> on branch claude/<basename> cut from fresh origin/main.
set -euo pipefail
RR=/Users/shawwalters/fees100-run
PK=$(cd "$1" && pwd); TITLE=$2; BODY=$3
NAME=$(basename "$PK"); BR=claude/$NAME
STAGE=$(mktemp -d); cp -R "$PK" "$STAGE/$NAME"
cd $RR/pr
git fetch -q origin main
git checkout -q --detach origin/main
git checkout -q -B "$BR" origin/main
git sparse-checkout add "research/$NAME"
rm -rf "research/$NAME"; mkdir -p research; cp -R "$STAGE/$NAME" "research/$NAME"; rm -rf "$STAGE"
find "research/$NAME" -name __pycache__ -type d -prune -exec rm -rf {} +
python3 -B "research/$NAME/verify.py" > /tmp/fees100-prverify.txt 2>&1 || { cat /tmp/fees100-prverify.txt; echo "verify failed"; exit 1; }
git add "research/$NAME"
git -c user.name=Shaw -c user.email=shawmakesmagic@gmail.com commit -q -m "$TITLE" -m "Adds research/$NAME only (research packet; no maintained source, status or workflow change)." -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push -q -u origin "$BR"
gh pr create --repo lalalune/pumpfun-source --base main --head "$BR" --title "$TITLE" --body-file "$BODY"
