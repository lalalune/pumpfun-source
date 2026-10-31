# Global initialization: prefunded CPI ordering

The recovered native `initialize` model at `9120883a957d7d9b2cab6140f66fb5bc9e6774d5` rejects every read-only user with `PrivilegeEscalation` and rejects an allocated Global before checking rent funding. Signed execution of the captured Pump image shows that prefunded Global accounts take a different order:

- An empty system-owned Global holding the full 8,463,360 lamport rent balance needs no transfer. With a read-only user, allocation and assignment are attempted before Anchor reports `ConstraintMut` (2000).
- An already allocated Global with insufficient rent first attempts the shortfall transfer. If the user cannot fund it, System error 1 precedes allocation's `AccountAlreadyInUse` (0).
- An already allocated, fully funded Global reports error 0 even when the user is read-only, because no transfer needs that user's write privilege.

The correction follows the rent transfer, allocation and user mutability checks in that order. A read-only Global still fails the System CPI, and a read-only user still fails a required transfer. Successful initialization retains its original bytes and balances.

The existing captured test now combines three Global layouts (empty system-owned, nonempty system-owned and program-owned), four prefunding balances, funded/zero-balance users and both account writability flags. These 96 additions produce 16 model mismatches before the correction and zero after. The existing 21 initialization controls also pass, and the complete 150-case lifecycle suite preserves toggles and authority rotation. Each failed initialization checks the unchanged Global and user balance; a zero-lamport user is absent in LiteSVM, as the existing custom-error checks already recognize.

The reproduction compiles the two native host source files from the requested revision, then executes the same 117 initialization cases against the captured ELF. There are no replacement CPI programs in this fixture. The captured image SHA-256 is `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`.

```sh
python -B research/global-initialize-cpi-order-20261101/reproduce.py --revision 9120883a957d7d9b2cab6140f66fb5bc9e6774d5 --output /tmp/global-init-before.json
python -B research/global-initialize-cpi-order-20261101/reproduce.py --output /tmp/global-init-after.json
python -B tests/test_global_lifecycle_captured.py
```

The runs use repository requirements and `rustc` on `PATH`; retained results used CPython 3.12.13, solders 0.27.1 and rustc 1.99.1. `results.json` records the source hashes, outcome counts and unchanged capture controls. This corrects the existing host model's error predictions under default rent and synthetic account states. It does not change the production SBF source or claim byte identity, arbitrary account-admission coverage, or live deployment behavior.
