#!/usr/bin/env python3
"""pump_amm sweep_protocol_fee / sweep_creator_fee: recipient validation, reserve-cover
check, empty bucket, accounting overflow and account-constraint paths, original vs
rebuilt image.

Each case builds a fresh LiteSVM with a synthetic GlobalConfig and Pool (accrued fees
written directly into the Pool account), a plain SPL Token quote mint and pool quote
vault, loads one pump_amm image plus LiteSVM's built-in SPL Token / Associated Token
programs, sends one sweep and records the error, compute units, full log list and the
post-state of the pool, the vault and the recipient ATA.

Usage: producer.py --root <repo> --images '{"original": P, "candidate": P}' --out <dir>
"""
import argparse, gzip, hashlib, json, pathlib, re, struct
from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

PROGRAM = Pubkey.from_string('pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
SYSTEM = Pubkey.default()
EVENT = Pubkey.find_program_address([b'__event_authority'], PROGRAM)[0]
PAYER = Keypair.from_seed(bytes([203]) * 32)
CREATOR = Pubkey.from_bytes(bytes([11]) * 32)
COIN_CREATOR = Pubkey.from_bytes(bytes([12]) * 32)
BASE = Pubkey.from_bytes(bytes([21]) * 32)
QUOTE = Pubkey.from_bytes(bytes([22]) * 32)
OTHER_MINT = Pubkey.from_bytes(bytes([26]) * 32)
LP = Pubkey.from_bytes(bytes([23]) * 32)
CONFIG = Pubkey.from_bytes(bytes([24]) * 32)
VBASE = Pubkey.from_bytes(bytes([34]) * 32)
VQUOTE = Pubkey.from_bytes(bytes([35]) * 32)
OTHER_VAULT = Pubkey.from_bytes(bytes([36]) * 32)
INDEX = 0
POOL, BUMP = Pubkey.find_program_address(
    [b'pool', INDEX.to_bytes(2, 'little'), bytes(CREATOR), bytes(BASE), bytes(QUOTE)], PROGRAM)
DISC = {False: hashlib.sha256(b'global:sweep_protocol_fee').digest()[:8],
        True: hashlib.sha256(b'global:sweep_creator_fee').digest()[:8]}
GLOBAL_DISC = bytes([149, 8, 156, 202, 160, 252, 176, 217])
POOL_DISC = bytes([241, 154, 109, 4, 17, 177, 109, 188])
MAX = 2**64 - 1
# protocol fee recipients 0x41.., 0x42.., ... 0x48.. (ascending, as binary_search needs)
RECIPIENTS = [Pubkey.from_bytes(bytes([0x41 + i]) * 32) for i in range(8)]
RESERVED = Pubkey.from_bytes(bytes([0x61]) * 32)
RESERVED_LIST = [Pubkey.from_bytes(bytes([0x71 + i]) * 32) for i in range(7)]
STRANGER = Pubkey.from_bytes(bytes([0x55]) * 32)


def creator_vault(cc):
    return Pubkey.find_program_address([b'creator_vault', bytes(cc)], PROGRAM)[0]


def ata(owner, m):
    return Pubkey.find_program_address([bytes(owner), bytes(TOKEN), bytes(m)], ATA)[0]


def mint(supply, decimals):
    d = bytearray(82)
    struct.pack_into('<I', d, 0, 1); d[4:36] = bytes([9]) * 32
    struct.pack_into('<Q', d, 36, supply); d[44] = decimals; d[45] = 1
    return bytes(d)


def token(m, owner, amount):
    d = bytearray(165); d[:32] = bytes(m); d[32:64] = bytes(owner)
    struct.pack_into('<Q', d, 64, amount); d[108] = 1
    return bytes(d)


def global_config(recipients):
    d = bytearray(949); d[:8] = GLOBAL_DISC; d[8:40] = bytes([5]) * 32
    struct.pack_into('<QQ', d, 40, 20, 5)
    for i, k in enumerate(recipients):
        d[57 + 32 * i:89 + 32 * i] = bytes(k)
    d[385:417] = bytes(RESERVED)
    for i, k in enumerate(RESERVED_LIST):
        d[418 + 32 * i:450 + 32 * i] = bytes(k)
    return bytes(d)


def pool(p):
    d = bytearray(287); d[:8] = POOL_DISC; d[8] = BUMP
    struct.pack_into('<H', d, 9, INDEX)
    for off, k in [(11, CREATOR), (43, BASE), (75, QUOTE), (107, LP), (139, VBASE), (171, VQUOTE), (211, p['cc'])]:
        d[off:off + 32] = bytes(k)
    struct.pack_into('<Q', d, 203, 10**9)
    d[243] = p['mayhem']
    d[245:261] = p['vqr'].to_bytes(16, 'little', signed=True)
    struct.pack_into('<QQ', d, 271, p['pf'], p['cf'])
    return bytes(d[:p['pool_len']]) if p['pool_len'] <= 287 else bytes(d) + bytes(p['pool_len'] - 287)


DEFAULT = dict(creator=False, pf=1000, cf=500, vault=10**6, vqr=0, mayhem=0, cc=COIN_CREATOR,
               recipient=RECIPIENTS[0], recipients=RECIPIENTS, pool_len=287, ata_exists=False,
               quote_mint=QUOTE, vault_key=VQUOTE, recipient_ata=None)


def cases():
    out = []
    def c(name, group, **kw):
        p = dict(DEFAULT); p.update(kw); p.update(name=name, group=group)
        out.append(p)
    # protocol bucket: recipient validation
    c('p-ok-recipient-0', 'protocol-recipient')
    c('p-ok-recipient-3', 'protocol-recipient', recipient=RECIPIENTS[3])
    c('p-ok-recipient-7', 'protocol-recipient', recipient=RECIPIENTS[7])
    c('p-recipient-stranger', 'protocol-recipient', recipient=STRANGER)
    c('p-recipient-default', 'protocol-recipient', recipient=Pubkey.default())
    c('p-recipient-default-listed', 'protocol-recipient', recipient=Pubkey.default(),
      recipients=[Pubkey.default()] + RECIPIENTS[1:])
    c('p-recipient-reserved-nonmayhem', 'protocol-recipient', recipient=RESERVED)
    c('p-recipient-creator-vault', 'protocol-recipient', recipient=creator_vault(COIN_CREATOR))
    c('p-unsorted-config-hit', 'protocol-recipient', recipient=RECIPIENTS[1],
      recipients=[RECIPIENTS[7]] + RECIPIENTS[1:7] + [RECIPIENTS[0]])
    c('p-unsorted-config-miss', 'protocol-recipient', recipient=RECIPIENTS[7],
      recipients=[RECIPIENTS[7]] + RECIPIENTS[1:7] + [RECIPIENTS[0]])
    c('p-unsorted-config-miss-0', 'protocol-recipient', recipient=RECIPIENTS[0],
      recipients=[RECIPIENTS[7]] + RECIPIENTS[1:7] + [RECIPIENTS[0]])
    c('p-mayhem-reserved', 'protocol-recipient', mayhem=1, recipient=RESERVED)
    c('p-mayhem-reserved-list-0', 'protocol-recipient', mayhem=1, recipient=RESERVED_LIST[0])
    c('p-mayhem-reserved-list-6', 'protocol-recipient', mayhem=1, recipient=RESERVED_LIST[6])
    c('p-mayhem-normal-recipient', 'protocol-recipient', mayhem=1, recipient=RECIPIENTS[0])
    c('p-mayhem-byte-2', 'protocol-recipient', mayhem=2, recipient=RESERVED)
    # creator bucket: recipient validation
    c('c-ok-vault', 'creator-recipient', creator=True, recipient=creator_vault(COIN_CREATOR))
    c('c-protocol-recipient', 'creator-recipient', creator=True, recipient=RECIPIENTS[0])
    c('c-coin-creator-itself', 'creator-recipient', creator=True, recipient=COIN_CREATOR)
    c('c-recipient-default', 'creator-recipient', creator=True, recipient=Pubkey.default())
    c('c-old-vault-after-change', 'creator-recipient', creator=True, cc=STRANGER,
      recipient=creator_vault(COIN_CREATOR))
    c('c-mayhem-vault', 'creator-recipient', creator=True, mayhem=1, recipient=creator_vault(COIN_CREATOR))
    # amounts, empty bucket, reserve cover
    c('p-empty-bucket', 'amounts', pf=0)
    c('c-empty-bucket', 'amounts', creator=True, cf=0, recipient=creator_vault(COIN_CREATOR))
    c('p-empty-both', 'amounts', pf=0, cf=0, vault=0)
    c('p-amount-1', 'amounts', pf=1, cf=0)
    c('p-cover-exact', 'amounts', vault=1500)
    c('p-cover-minus-1', 'amounts', vault=1499)
    c('p-empty-cover-fails', 'amounts', pf=0, cf=10, vault=9)
    c('c-cover-minus-1', 'amounts', creator=True, vault=1499, recipient=creator_vault(COIN_CREATOR))
    c('p-fee-sum-overflow', 'amounts', pf=MAX, cf=1, vault=MAX)
    c('p-pf-max', 'amounts', pf=MAX, cf=0, vault=MAX)
    c('p-vqr-negative', 'amounts', vqr=-1500)
    c('p-vqr-add-overflow', 'amounts', vqr=2**127 - 1000)
    c('p-vqr-add-exact-max', 'amounts', vqr=2**127 - 1001)
    c('p-recipient-ata-exists', 'amounts', ata_exists=True)
    # account constraints and pool length
    c('p-wrong-quote-mint', 'accounts', quote_mint=OTHER_MINT)
    c('p-wrong-pool-vault', 'accounts', vault_key=OTHER_VAULT)
    c('p-recipient-ata-wrong', 'accounts', recipient_ata=OTHER_VAULT)
    c('p-pool-len-300', 'accounts', pool_len=300)
    c('p-pool-len-286', 'accounts', pool_len=286)
    c('p-pool-len-279', 'accounts', pool_len=279)
    c('p-pool-len-243', 'accounts', pool_len=243)
    return out


def run_case(p, image):
    vm = LiteSVM().with_transaction_history(0)
    if isinstance(image, bytes):
        vm.add_program(PROGRAM, image)
    else:
        vm.add_program_from_file(PROGRAM, image)
    vm.set_clock(Clock(100, 1234567890, 0, 0, 1234567890))
    vm.airdrop(PAYER.pubkey(), 10**12)
    vm.set_account(EVENT, Account(10**9, b'', Pubkey.default()))
    vm.set_account(CONFIG, Account(10**9, global_config(p['recipients']), PROGRAM))
    pd = pool(p)
    vm.set_account(POOL, Account(10**7, pd, PROGRAM))
    vm.set_account(QUOTE, Account(10**9, mint(MAX, 9), TOKEN))
    vm.set_account(OTHER_MINT, Account(10**9, mint(MAX, 9), TOKEN))
    vm.set_account(VQUOTE, Account(10**9, token(QUOTE, POOL, p['vault']), TOKEN))
    vm.set_account(OTHER_VAULT, Account(10**9, token(QUOTE, POOL, p['vault']), TOKEN))
    rata = ata(p['recipient'], p['quote_mint']) if p['recipient_ata'] is None else p['recipient_ata']
    if p['ata_exists']:
        vm.set_account(rata, Account(10**9, token(QUOTE, p['recipient'], 7), TOKEN))
    metas = [AccountMeta(k, s, w) for k, s, w in [
        (PAYER.pubkey(), True, True), (CONFIG, False, False), (POOL, False, True), (p['quote_mint'], False, False),
        (TOKEN, False, False), (p['vault_key'], False, True), (p['recipient'], False, False), (rata, False, True),
        (SYSTEM, False, False), (ATA, False, False), (EVENT, False, False), (PROGRAM, False, False)]]
    tx = Transaction.new_signed_with_payer([Instruction(PROGRAM, DISC[p['creator']], metas)], PAYER.pubkey(), [PAYER],
                                           vm.latest_blockhash())
    r = vm.send_transaction(tx)
    failed = isinstance(r, FailedTransactionMetadata)
    meta = r.meta() if failed else r
    cu = meta.compute_units_consumed
    cu = cu() if callable(cu) else cu
    state = {}
    pa = vm.get_account(POOL)
    state['pool'] = bytes(pa.data).hex(); state['pool_lamports'] = str(pa.lamports)
    for role, k in (('vault', VQUOTE), ('recipient_ata', rata)):
        acc = vm.get_account(k)
        state[role] = None if acc is None or len(bytes(acc.data)) < 72 else str(struct.unpack_from('<Q', bytes(acc.data), 64)[0])
    state['payer_lamports'] = str(vm.get_account(PAYER.pubkey()).lamports)
    return {'error': str(r.err()) if failed else None, 'cu': cu, 'logs': list(meta.logs()), 'state': state}


def anchor_code(logs):
    for line in logs:
        if 'Error Code: ' in line:
            return line.split('Error Code: ')[1].split('.')[0]
        if 'panicked' in line:
            return 'panic'
    return None


def program_logs(logs):
    return [l for l in logs if not ('consumed' in l and 'compute units' in l)]


def observed(p, rec):
    s = rec['state']
    pd = bytes.fromhex(s['pool'])
    o = {'pool_len': len(pd), 'vault_delta': None if s['vault'] is None else str(int(s['vault']) - p['vault']),
         'recipient_ata': s['recipient_ata'],
         'nothing_to_sweep_log': next((l for l in rec['logs'] if 'Nothing to sweep' in l), None)}
    if len(pd) >= 287:
        o.update(protocol_fees=str(struct.unpack_from('<Q', pd, 271)[0]), creator_fees=str(struct.unpack_from('<Q', pd, 279)[0]),
                 virtual_quote_reserves=str(int.from_bytes(pd[245:261], 'little', signed=True)))
    return o


PREFIX = b'programs/pump-amm/'


def strip_prefix(blob):
    """Control image: the original with every reference to a 'programs/pump-amm/src/*.rs' string
    moved 18 bytes later (past the prefix) and the matching length immediate lowered by 18,
    so its AnchorError file names read 'src/...' like the rebuild's. Nothing else changes."""
    b = bytearray(blob)
    secs = elf_sections(bytes(b))
    ro_off, ro_len = secs['.rodata']; tx_off, tx_len = secs['.text']
    starts = {}
    for m in re.finditer(re.escape(PREFIX) + rb'src/[A-Za-z0-9_/]+\.rs', bytes(b[ro_off:ro_off + ro_len])):
        starts[ro_off + m.start()] = len(m.group(0))
    sites = 0
    for i in range(tx_off, tx_off + tx_len - 16, 8):
        if b[i] != 0x18:
            continue
        imm = struct.unpack_from('<I', b, i + 4)[0] | (struct.unpack_from('<I', b, i + 12)[0] << 32)
        if imm not in starts:
            continue
        n = starts[imm]
        for j in range(i + 16, i + 16 + 8 * 12, 8):
            if b[j] in (0x7a, 0x62, 0xb7, 0xb4) and struct.unpack_from('<i', b, j + 4)[0] == n:
                struct.pack_into('<i', b, j + 4, n - len(PREFIX))
                new = imm + len(PREFIX)
                struct.pack_into('<I', b, i + 4, new & 0xffffffff); struct.pack_into('<I', b, i + 12, new >> 32)
                sites += 1
                break
    return bytes(b), sites


def elf_sections(blob):
    shoff, = struct.unpack_from('<Q', blob, 0x28)
    shentsize, shnum, shstrndx = struct.unpack_from('<HHH', blob, 0x3a)
    hs = [struct.unpack_from('<IIQQQQIIQQ', blob, shoff + i * shentsize) for i in range(shnum)]
    st = hs[shstrndx]; names = blob[st[4]:st[4] + st[5]]
    return {names[h[0]:names.index(b'\0', h[0])].decode(): (h[4], h[5]) for h in hs if h[0]}


def jsonable(v):
    if isinstance(v, Pubkey):
        return str(v)
    if isinstance(v, list):
        return [jsonable(x) for x in v]
    if isinstance(v, int) and not isinstance(v, bool) and abs(v) >= 2**53:
        return str(v)
    return v


def produce(images):
    stripped, _ = strip_prefix(pathlib.Path(images['original']).read_bytes())
    rows = []
    for p in cases():
        rec = {'case': p['name'], 'group': p['group'], 'instruction': 'sweep_creator_fee' if p['creator'] else 'sweep_protocol_fee',
               'params': {k: jsonable(v) for k, v in p.items() if k not in ('name', 'group')}}
        for tag in ('original', 'candidate'):
            rec[tag] = run_case(p, images[tag])
        s = run_case(p, stripped)
        o, c = rec['original'], rec['candidate']
        rec['stripped_original'] = {'cu': s['cu'], 'same_error_state_as_candidate': (s['error'], s['state']) == (c['error'], c['state']),
                                    'same_logs_as_candidate': s['logs'] == c['logs']}
        rec['same_error'] = o['error'] == c['error']
        rec['same_state'] = o['state'] == c['state']
        rec['same_logs_ex_cu'] = program_logs(o['logs']) == program_logs(c['logs'])
        rec['same_logs'] = o['logs'] == c['logs']
        norm = lambda logs: [l.replace('thrown in programs/pump-amm/src/', 'thrown in src/') for l in program_logs(logs)]
        rec['same_logs_path_normalized'] = norm(o['logs']) == norm(c['logs'])
        rec['cu_delta'] = c['cu'] - o['cu']
        rec['anchor_error'] = {'original': anchor_code(o['logs']), 'candidate': anchor_code(c['logs'])}
        rec['error_site'] = {t: next((l.split('AnchorError thrown in ')[1].split('. Error Code')[0]
                                      for l in rec[t]['logs'] if 'AnchorError thrown in ' in l), None)
                             for t in ('original', 'candidate')}
        rec['observed'] = observed(p, o)
        rows.append(rec)
    return rows


def sha_file(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def summarize(images, rows, body):
    st = strip_prefix(pathlib.Path(images['original']).read_bytes())
    return {
        'image_sha256': {k: sha_file(v) for k, v in images.items()},
        'case_count': len(rows),
        'success_count': sum(r['original']['error'] is None for r in rows),
        'behavior_match': sum(r['same_error'] and r['same_state'] for r in rows),
        'log_match_ex_cu': sum(r['same_logs_ex_cu'] for r in rows),
        'log_match_exact': sum(r['same_logs'] for r in rows),
        'log_match_path_normalized': sum(r['same_logs_path_normalized'] for r in rows),
        'cu_delta_histogram': {str(d): sum(r['cu_delta'] == d for r in rows) for d in sorted({r['cu_delta'] for r in rows})},
        'cu_equal': sum(r['cu_delta'] == 0 for r in rows),
        'cases': [{'case': r['case'], 'group': r['group'], 'instruction': r['instruction'], 'error': r['original']['error'],
                   'anchor_error': r['anchor_error'], 'cu_original': r['original']['cu'],
                   'cu_candidate': r['candidate']['cu'], 'cu_delta': r['cu_delta'],
                   'same_error': r['same_error'], 'same_state': r['same_state'],
                   'same_logs_ex_cu': r['same_logs_ex_cu'], 'error_site': r['error_site'],
                   'observed': r['observed']} for r in rows],
        'receipts_sha256': hashlib.sha256(body).hexdigest(),
        'stripped_original_control': {
            'sites_patched': st[1], 'sha256': hashlib.sha256(st[0]).hexdigest(),
            'cu_equal_to_candidate': sum(r['stripped_original']['cu'] == r['candidate']['cu'] for r in rows),
            'logs_equal_to_candidate': sum(r['stripped_original']['same_logs_as_candidate'] for r in rows),
            'error_state_equal_to_candidate': sum(r['stripped_original']['same_error_state_as_candidate'] for r in rows),
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--images', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    images = json.loads(a.images)
    rows = produce(images)
    out = pathlib.Path(a.out) / 'runtime'
    out.mkdir(parents=True, exist_ok=True)
    body = ''.join(json.dumps(r, sort_keys=True, separators=(',', ':')) + '\n' for r in rows).encode()
    (out / 'receipts.jsonl.gz').write_bytes(gzip.compress(body, mtime=0))
    summary = summarize(images, rows, body)
    rep = json.dumps(summary, sort_keys=True, indent=1).encode()
    (out / 'report.json.gz').write_bytes(gzip.compress(rep, mtime=0))
    print(json.dumps({k: summary[k] for k in ('case_count', 'success_count', 'behavior_match', 'log_match_ex_cu',
                                              'log_match_exact', 'log_match_path_normalized', 'cu_equal',
                                              'cu_delta_histogram', 'stripped_original_control')}))


if __name__ == '__main__':
    main()
