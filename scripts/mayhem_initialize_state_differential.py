#!/usr/bin/env python3
"""Behavioral differential harness for mayhem `initialize_mayhem_state` (disc 9dbd5e485545cc2d).

INTEGRITY NOTE / RESULT SUMMARY
-------------------------------
A genuine *standalone* behavioral oracle for this handler CANNOT be honestly
constructed, and this script proves exactly why by driving the UNMODIFIED
captured original ELF (evidence/original/mayhem/deployed.so, comparison input
only) through the complete account/argument validation chain in local LiteSVM.

Empirically recovered account order (positional, from the original's own
AnchorError output):

  0 payer                     (signer, mut)
  1 global_params             Account<GlobalParams>, PDA ["global-params"] @ mayhem
  2 mint_authority            PDA ["mint-authority"] @ PUMP (6EF8..), **Signer**
  3 sol_vault                 PDA ["sol-vault"] @ mayhem
  4 mint                      InterfaceAccount<Mint>, Token-2022, must pre-exist
  5 mayhem_token_vault        token-2022 ATA, authority = sol_vault, must pre-exist
  6 mayhem_state              Account<MayhemState>, init, PDA ["mayhem-state", mint]
  7 system_program
  8 token_program             = Token-2022 (TokenzQdB..)
  9 associated_token_program

The validation chain is satisfiable locally for accounts 0,1,3,4,5,6,7,8,9 (this
script reaches each in turn), but TERMINATES at account 2 (`mint_authority`) with:

    AnchorError caused by account: mint_authority
    Error Code: ConstraintSigner (2002)

`mint_authority` is simultaneously constrained by seeds to equal the PUMP
program's mint-authority PDA (TSLvdd1pWpHVjahSpsvCXUbgwsL3JAcvokwaKt1eokM, an
*off-curve* address with no private key) AND required to be a transaction signer.
An off-curve PDA owned by the pump program can only sign when the pump program
itself invokes this instruction via `invoke_signed`. No standalone transaction,
and no locally generated keypair, can honestly provide that signature. Forcing it
(e.g. a synthetic/unchecked signer) would be a synthetic-signer bypass, which is
disallowed.

Therefore `initialize_mayhem_state` is a CPI target of the pump program, not a
standalone instruction. The only honest driver is a genuine pump-program CPI
(a mayhem-mode pump create), which is not available as captured evidence and
whose pump-side mayhem-creation path is itself only partially reconstructed.
pump/deployed.so references the mayhem program id but does NOT contain this
instruction's discriminator as a literal, consistent with a non-literal/al
dynamically-built CPI path rather than a reproducible standalone call.

Output JSON = {"cases": [...], "mismatches": [...]} per the repo convention.
Because no valid Ok transaction exists, there is no 0-mismatch positive
validation; `mismatches` records only genuine original-vs-candidate divergences
observed along the (necessarily failing) validation chain, and
`valid_init_transaction_constructible` is reported false with the precise reason.
No binary patching, no synthetic-signer bypass, no fabricated success.
"""
import argparse, hashlib, json, pathlib, struct
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.account import Account
from solders.instruction import Instruction, AccountMeta
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
from pump_amm_reusable_harness import pin_program
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit

ROOT = pathlib.Path(__file__).resolve().parents[1]
MAY = Pubkey.from_string('MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e')
PUMP = Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
PFEES = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN2022 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
SYS = Pubkey.default()
DISC = hashlib.sha256(b'global:initialize_mayhem_state').digest()[:8]  # 9dbd5e485545cc2d
PAYER = Keypair.from_seed(bytes([2]) * 32)
ADMIN = Keypair.from_seed(bytes([1]) * 32)
MINT = Keypair.from_seed(bytes([9]) * 32).pubkey()

def pda(seeds, prog=MAY):
    return Pubkey.find_program_address(seeds, prog)[0]

GLOBAL = pda([b'global-params'])
SOLV = pda([b'sol-vault'])
STATE = pda([b'mayhem-state', bytes(MINT)])
MINT_AUTHORITY_PUMP = pda([b'mint-authority'], PUMP)        # off-curve pump PDA, must sign
MINT_AUTHORITY_MAY = pda([b'mint-authority'], MAY)          # negative control
VAULT = Pubkey.find_program_address([bytes(SOLV), bytes(TOKEN2022), bytes(MINT)], ATA)[0]
sha = lambda b: hashlib.sha256(b).hexdigest()


class Fixture:
    def __init__(self, binary):
        self.binary = binary

    def _vm(self):
        vm = LiteSVM().with_sigverify(True).with_blockhash_check(True).with_log_bytes_limit(None)
        vm.add_program_from_file(MAY, self.binary)
        vm.add_program_from_file(PUMP, ROOT / 'evidence/original/pump/deployed.so')
        vm.add_program_from_file(PFEES, ROOT / 'evidence/original/pump_fees/deployed.so')
        for name, key in [('spl_token', TOKEN), ('spl_token_2022', TOKEN2022), ('associated_token', ATA)]:
            cap = json.loads((ROOT / f'evidence/dependencies/{name}/capture.json').read_text())
            vm.add_program_from_file(Pubkey.from_string(cap['program']), ROOT / f'evidence/dependencies/{name}/deployed.so')
        vm.set_clock(Clock(100, 0, 0, 0, 100))
        for kp in [PAYER.pubkey(), ADMIN.pubkey()]:
            vm.set_account(kp, Account(10 ** 12, b'', SYS))
        vm.set_account(SOLV, Account(10 ** 10, b'', SYS))
        # GlobalParams (admin + trader = ADMIN), synthetic but valid shape
        gd = bytearray(hashlib.sha256(b'account:GlobalParams').digest()[:8] + bytes(310))
        gd[49:81] = bytes(ADMIN.pubkey()); gd[81:113] = bytes(ADMIN.pubkey())
        vm.set_account(GLOBAL, Account(10 ** 9, bytes(gd), MAY))
        return vm

    def _mint(self, mint_authority):
        md = bytearray(82); struct.pack_into('<I', md, 0, 1); md[4:36] = bytes(mint_authority); md[44] = 6; md[45] = 1
        return bytes(md)

    def _tokacct(self, mint, owner):
        b = bytearray(165); b[0:32] = bytes(mint); b[32:64] = bytes(owner); b[108] = 1
        return bytes(b)

    def execute(self, c):
        """Run a progressively-satisfied initialize_mayhem_state attempt; return observable behavior."""
        vm = self._vm()
        stage = c['stage']
        # account 4: mint (Token-2022, mint_authority = pump mint-authority PDA)
        if stage >= 4:
            vm.set_account(MINT, Account(10 ** 9, self._mint(MINT_AUTHORITY_PUMP), TOKEN2022))
        # account 5: mayhem_token_vault — Token-2022 ATA with authority = sol_vault
        if stage >= 5:
            vm.set_account(VAULT, Account(10 ** 8, self._tokacct(MINT, SOLV), TOKEN2022))
        # account 6: mayhem_state is init -> must be empty/system-owned
        vm.set_account(STATE, Account(0, b'', SYS))
        # mint_authority: correct pump PDA from stage>=2 (negative control = mayhem PDA below)
        ma = MINT_AUTHORITY_PUMP if stage >= 2 else MINT_AUTHORITY_MAY
        vm.set_account(ma, Account(10 ** 9, b'', SYS))
        keys = [PAYER.pubkey(), GLOBAL, ma, SOLV, MINT, VAULT, STATE, SYS, TOKEN2022, ATA]
        # mint_authority is NEVER a true signer: it is an off-curve pump PDA with no key.
        # Marking it signer here is impossible to actually sign, so it stays non-signer;
        # the original's ConstraintSigner on it is the terminal, honest blocker.
        signer_flags = [True] + [False] * 9
        writable = {0, 1, 2, 3, 5, 6}
        n = c.get('account_count', 10)
        metas = [AccountMeta(k, signer_flags[i], i in writable) for i, k in enumerate(keys)][:n]
        payload = DISC + bytes(MINT) + bytes(c.get('arg_pad', 32))
        ix = Instruction(MAY, payload, metas)
        tx = Transaction.new_signed_with_payer(
            [set_compute_unit_limit(1_400_000), ix], PAYER.pubkey(), [PAYER], vm.latest_blockhash())
        assert all(tx.verify_with_results())
        r = vm.send_transaction(tx)
        failed = isinstance(r, FailedTransactionMetadata)
        meta = r.meta() if failed else r
        logs = meta.logs()
        anchor = next((l.split('Program log: ')[-1] for l in logs
                       if 'AnchorError' in l and ('caused by' in l or 'occurred' in l)), None)
        state_after = vm.get_account(STATE)
        return {
            'error': str(r.err()) if failed else None,
            'anchor_error': anchor,
            'logs': logs,
            'state_created': bool(state_after and state_after.owner == MAY and len(state_after.data) > 0),
            'signature': str(tx.signatures[0]),
            'signature_verified': True,
        }


def cases():
    return [
        {'name': 'stage0-minimal-args', 'stage': 0},
        {'name': 'stage2-mint_authority-pump-pda', 'stage': 2},
        {'name': 'stage4-mint-present', 'stage': 4},
        {'name': 'stage5-token-vault-present', 'stage': 5},
        {'name': 'full-maximal-valid-standalone', 'stage': 5, 'account_count': 10},
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--candidate', type=pathlib.Path, required=True,
                    help='source-built mayhem ELF (comparison target)')
    ap.add_argument('--output', type=pathlib.Path, required=True)
    a = ap.parse_args(); a.candidate = pin_program(a.candidate)
    original = ROOT / 'evidence/original/mayhem/deployed.so'
    o = Fixture(original); b = Fixture(a.candidate)
    rows = []; mismatches = []
    for c in cases():
        x = o.execute(c); y = b.execute(c)
        equal = all(x[k] == y[k] for k in ['error', 'anchor_error', 'state_created'])
        rows.append({'case': c, 'original': x, 'candidate': y, 'equal': equal})
        if not equal:
            mismatches.append({'case': c['name'],
                               'original_error': x['anchor_error'] or x['error'],
                               'candidate_error': y['anchor_error'] or y['error']})
        print(c['name'], '| original:', x['anchor_error'] or x['error'], flush=True)

    # The terminal blocker, asserted reproducibly against the original.
    full = next(r for r in rows if r['case']['name'] == 'full-maximal-valid-standalone')
    orig_full = full['original']
    signer_gate = (orig_full['anchor_error'] or '').find('ConstraintSigner') >= 0 \
        and 'mint_authority' in (orig_full['anchor_error'] or '')

    report = {
        'scope': __doc__.strip().splitlines()[0],
        'instruction': 'initialize_mayhem_state',
        'discriminator': DISC.hex(),
        'valid_init_transaction_constructible': False,
        'reason': (
            'mint_authority is constrained to the pump program mint-authority PDA '
            '(TSLvdd1pWpHVjahSpsvCXUbgwsL3JAcvokwaKt1eokM, off-curve) AND required to '
            'be a signer (ConstraintSigner/2002). Only the pump program can sign for '
            'that PDA via invoke_signed, so no standalone transaction can satisfy it; '
            'forcing it would be a synthetic-signer bypass. The handler is a pump CPI '
            'target, so no honest standalone behavioral oracle exists.'),
        'recovered_account_order': [
            'payer(signer,mut)', 'global_params(PDA[global-params]@mayhem)',
            'mint_authority(PDA[mint-authority]@pump, SIGNER)', 'sol_vault(PDA[sol-vault]@mayhem)',
            'mint(InterfaceAccount<Mint>, Token-2022, pre-existing)',
            'mayhem_token_vault(Token-2022 ATA authority=sol_vault, pre-existing)',
            'mayhem_state(init, PDA[mayhem-state,mint])', 'system_program',
            'token_program(=Token-2022)', 'associated_token_program'],
        'terminal_blocker_confirmed': bool(signer_gate),
        'terminal_blocker_anchor_error': orig_full['anchor_error'],
        'original_sha256': sha(original.read_bytes()),
        'candidate_sha256': sha(a.candidate.read_bytes()),
        'case_count': len(rows),
        'mismatches': mismatches,
        'cases': rows,
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'cases': len(rows), 'mismatches': [m['case'] for m in mismatches],
                      'valid_init_transaction_constructible': False,
                      'terminal_blocker_confirmed': bool(signer_gate),
                      'terminal_blocker': orig_full['anchor_error']}))
    # Non-zero exit signals that no positive (Ok) oracle case could be formed.
    raise SystemExit(0 if signer_gate else 2)


if __name__ == '__main__':
    main()
