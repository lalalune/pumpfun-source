# Replay the public multiline probe

Use an existing clean checkout with the pinned dependencies and Chromium already
available. Public source `1d019c45b7abf5b6003927d666a868ce47ed1043` has complete
tree `6c9aa89838bee28c94861855e63051eb6603fa59`, identical to historically
measured `8239192d14107040b0f4f468ed69ce8136323219`. Public receipt commit
`197826af1930dbd4af6dd4d3bd2687719b9ca04c` supplies the exact executed probe,
config and retained-test port patch. The source commit intentionally has no
new permanent test suite; fetch the receipt bytes separately as shown below.

Run this whole block from the repository root. It collects the three finite
cases without starting Next or a browser. To execute them, uncomment the marked
browser command before running the block, with port 3027 free. These are
candidate replay commands, not a rerun of the historical base comparison.

The sequence records the starting commit and leaves the checkout detached at
the exact public source. Its subshell avoids changing the caller's cwd/traps.
Temporary files are created exclusively and removed on exit; a fresh external
directory retains the executed copies, reports and failures. Existing receipt,
artifact and dependency directories are never used as output locations.

```sh
(
set -e
test -z "$(git status --porcelain)"
git rev-parse HEAD
git fetch --no-tags --depth=1 --filter=blob:none \
  https://github.com/shawkkkkk/pumpfun-source.git \
  1d019c45b7abf5b6003927d666a868ce47ed1043 \
  197826af1930dbd4af6dd4d3bd2687719b9ca04c
git switch --detach 1d019c45b7abf5b6003927d666a868ce47ed1043
test "$(git rev-parse 'HEAD^{tree}')" = 6c9aa89838bee28c94861855e63051eb6603fa59
DESCRIPTION_REPLAY_REPO="$(pwd -P)"
DESCRIPTION_REPLAY_OUTPUT="$(mktemp -d)"
python3 - "$DESCRIPTION_REPLAY_REPO" "$DESCRIPTION_REPLAY_OUTPUT" <<'PY'
import json, pathlib, subprocess, sys
repo, output = map(pathlib.Path, sys.argv[1:])
receipt = '197826af1930dbd4af6dd4d3bd2687719b9ca04c'
prefix = 'app/reconstruction/create-description-lines/validation/'
def read(name):
    return subprocess.check_output(['git', 'show', receipt + ':' + prefix + name], cwd=repo)
spec = read('finite.spec.ts.txt')
config = read('executed-candidate.config.ts.txt').decode()
for name in ['report-candidate.json', 'browser-candidate']:
    old = json.dumps('/workspace/pump-create-description-lines-audit/' + name)
    assert config.count(old) == 1
    config = config.replace(old, json.dumps(str(output / name)))
assert '/workspace/pump-create-description-lines-audit' not in config
frontend = repo / 'app/packages/frontend'
files = {
    output / 'executed-spec.ts.txt': spec,
    output / 'executed-config.ts.txt': config.encode(),
    output / 'retained-port-only.patch': read('retained-port-only.patch'),
    frontend / 'tests/create-description-lines.tmp.spec.ts': spec,
    frontend / 'playwright.create-description-lines.tmp.config.ts': config.encode(),
}
assert all(not path.exists() for path in files)
for path, data in files.items():
    with path.open('xb') as stream:
        stream.write(data)
PY
cleanup_description_replay() {
  rm -f "$DESCRIPTION_REPLAY_REPO/app/packages/frontend/tests/create-description-lines.tmp.spec.ts" \
    "$DESCRIPTION_REPLAY_REPO/app/packages/frontend/playwright.create-description-lines.tmp.config.ts"
  git -C "$DESCRIPTION_REPLAY_REPO" restore \
    --source=1d019c45b7abf5b6003927d666a868ce47ed1043 -- \
    app/packages/frontend/tests/create.spec.ts app/packages/frontend/next-env.d.ts
}
trap cleanup_description_replay EXIT
cd "$DESCRIPTION_REPLAY_REPO/app/packages/frontend"
corepack pnpm exec playwright test \
  --config playwright.create-description-lines.tmp.config.ts \
  tests/create-description-lines.tmp.spec.ts --list \
  > "$DESCRIPTION_REPLAY_OUTPUT/collection.log" 2>&1

# Optional actual three-case browser replay (port 3027 must be free):
# corepack pnpm exec playwright test \
#   --config playwright.create-description-lines.tmp.config.ts \
#   tests/create-description-lines.tmp.spec.ts \
#   > "$DESCRIPTION_REPLAY_OUTPUT/browser.log" 2>&1

printf 'Retained outputs: %s\n' "$DESCRIPTION_REPLAY_OUTPUT"
)
```

Expected collection: three cases. The historical candidate also ran all eleven
existing Create controls. To include them, before the subshell's closing line,
apply the public patch using
`git -C "$DESCRIPTION_REPLAY_REPO" apply --directory=app/packages/frontend "$DESCRIPTION_REPLAY_OUTPUT/retained-port-only.patch"`
and add `tests/create.spec.ts` to the Playwright command (14 cases). The patch
only changes the retained test's strict loopback origin from 3010 to 3027;
cleanup restores the exact pinned test afterward. If running both the three-case
and fourteen-case cohorts, use `--output "$DESCRIPTION_REPLAY_OUTPUT/controls14"`
and `PLAYWRIGHT_JSON_OUTPUT_FILE="$DESCRIPTION_REPLAY_OUTPUT/controls14.json"`
for the second command so it preserves the first command's report/artifacts.

Both the repository and output paths may contain spaces; argument arrays,
quoted shell paths and JSON string encoding retain them. No historical config,
probe, screenshot, result or source guard is changed. Collection and public
source/fixture loading are portability checks; the retained browser results
remain the separately qualified historical runs.
