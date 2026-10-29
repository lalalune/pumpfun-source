# Input-hash and CI follow-up

The limited review of public commit `440a495d4c37625f4f5b321d2d54df83475a62da`
asked whether three values in `work-record.json` were placeholders and requested
normal repository CI. The published record actually contains eleven lowercase,
64-digit SHA-256 values. Fresh byte verification matches all eleven, including
the installed React type declaration. [input-audit.json](input-audit.json)
records their exact paths, sizes and digests. Reproduce it with:

```sh
python3 app/reconstruction/search-pointer-dismissal/verify-inputs.py
```

The verifier authenticates the original work record's SHA-256 before reading
its declared inputs. The original work record, browser observations, logs,
screenshots and manifest remain unchanged. This audit is an appended provenance
check, not a replacement measurement or a new browser run. It does not claim a
complete dependency closure.

The PR title and this follow-up commit omit the CI-skip directive so normal
repository checks can run. Their eventual result must be read from the checks
on the new public head; the earlier local and root checks are not relabelled as
GitHub CI results.
