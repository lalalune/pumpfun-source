This is a finite mounted-page receipt, not an aggregate build receipt. Run from
the repository root:

    python3 app/reconstruction/competition-prize-page/qualification/verify.py

`record.json` binds the exact published source commit/tree and 47 relevant Git
inputs. The baseline copies equal their named base Git blobs. `source-swap.py`
and `playwright.config.executed.ts` are the exact local tools used, retaining
absolute workspace paths as execution evidence; they are not automatic setup
scripts. Review them before adapting to another checkout.

To repeat on another checkout with existing pinned dependencies:

1. Run the source/23-test/typecheck/integrity commands in the package README.
2. Copy `playwright.config.executed.ts` to a temporary file and replace only its
   repository/test/output paths with the local checkout and a temporary output
   directory. Preserve its one-worker, zero-retry, browser, viewport/test and
   storage-state settings. Set the Chromium executable to the installed matching
   browser, or omit that override to use Playwright's matching installed browser.
3. Start the frontend from `app/packages/frontend` with the `serverArgv` and
   `serverEnv` in `record.json`. Choose a free loopback port and use that same
   origin in the temporary config. No backend server is used; the test intercepts
   local adapter reads and rejects foreign origins and mutations.
4. Save the candidate page/model, replace those two files with `../reference/`
   copies, restart Next, and run the recorded baseline browser command. Both
   empty-standings cases should fail at the absent Prize breakdown region after
   the actual detail heading is visible. Restore the exact saved candidate files,
   restart Next, then run all five cases with the same final harness/config.
   Do not replace unknown local edits. The candidate result here is 5/5 passes.
5. Stop the owned server. Retain raw logs/screenshots before removing generated
   caches. Do not rewrite captures, dependencies or another checkout.

The first fixed raw report is retained separately: 2 passes/3 harness failures.
Those failures prompted actual Filter submission and comparison across local
read actions rather than requiring one initial StrictMode read. The final
baseline and fixed reports both use the exact source-bound final spec. There
were no corresponding product changes. The initial harness is not presented as
an independently sealed source revision.

The public PNGs show real before-page and fixed widget captures at 390/1280px.
Raw videos and additional screenshots remain in private local staging. No full
app/browser, production build, private backend or original provider parity is
inferred from these finite results. Common root evidence/tooling checks are
reported separately on the exact published leaf.
