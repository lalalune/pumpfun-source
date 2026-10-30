#!/usr/bin/env python3
"""pump_amm admin_cto_pool: check order, holder-reward / cashback / quote gates, fee bounds.

admin_cto_pool makes no CPI except the System transfer in prepare_pool, so it is
called directly: a fresh LiteSVM per case with signature verification off, the Pump
pool-authority PDA of the base mint placed in the signer slot, and synthetic
GlobalConfig / Pool accounts. Each case records the error, compute units, full logs
and post-state bytes of the pool, on the original and on the rebuilt image.

Usage: producer.py --root <repo> --images '{"original": P, "candidate": P}' --out <dir>
"""
import argparse, gzip, hashlib, json, pathlib, re, struct
from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

PROGRAM = Pubkey.from_string('pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA')
PUMP = Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
SYSTEM = Pubkey.from_string('11111111111111111111111111111111')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
USDC = Pubkey.from_string('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v')
EVENT = Pubkey.find_program_address([b'__event_authority'], PROGRAM)[0]
PAYER = Keypair.from_seed(bytes([203]) * 32)
BASE = Pubkey.from_bytes(bytes([41]) * 32)
QUOTE = Pubkey.from_bytes(bytes([42]) * 32)
CONFIG = Pubkey.from_bytes(bytes([44]) * 32)
POOL = Pubkey.from_bytes(bytes([45]) * 32)
OLD_CC = Pubkey.from_bytes(bytes([46]) * 32)
NEW_CC = Pubkey.from_bytes(bytes([47]) * 32)
OTHER = Pubkey.from_bytes(bytes([48]) * 32)
PA = Pubkey.find_program_address([b'pool-authority', bytes(BASE)], PUMP)[0]
HR = Pubkey.find_program_address([b'holder-rewards', bytes(BASE)], PUMP)[0]
DISC = hashlib.sha256(b'global:admin_cto_pool').digest()[:8]
GLOBAL_DISC = bytes([149, 8, 156, 202, 160, 252, 176, 217])
POOL_DISC = bytes([241, 154, 109, 4, 17, 177, 109, 188])
NAMED = {'NEW_CC': NEW_CC, 'HR': HR, 'OTHER': OTHER, 'PA': PA, 'WSOL': WSOL, 'USDC': USDC, 'QUOTE': QUOTE}

DEFAULT = dict(cc='NEW_CC', holder=False, fee=None, configurable=1, max_bps=1000,
               creator='PA', quote='QUOTE', mayhem=0, cashback=0, pool_holder=0, can_edit=1,
               creator_fees=0, old_fee=50, pool_len=300, pool_lamports=10**9,
               pa_signer=True, pa_key='PA', payload=None, config_disc_ok=True, config_len=949)


def global_config(p):
    d = bytearray(max(p['config_len'], 949)); d[:8] = GLOBAL_DISC if p['config_disc_ok'] else bytes(8)
    d[8:40] = bytes([5]) * 32; d[940] = p['configurable']; struct.pack_into('<Q', d, 941, p['max_bps'])
    return bytes(d[:p['config_len']])


def pool(p):
    d = bytearray(300); d[:8] = POOL_DISC; d[8] = 255
    for off, k in [(11, NAMED[p['creator']]), (43, BASE), (75, NAMED[p['quote']]), (211, OLD_CC)]:
        d[off:off + 32] = bytes(k)
    struct.pack_into('<Q', d, 203, 10**10)
    d[243] = p['mayhem']; d[244] = p['cashback']
    struct.pack_into('<Q', d, 261, p['old_fee']); d[269] = p['can_edit']; d[270] = p['pool_holder']
    struct.pack_into('<QQ', d, 271, 0, p['creator_fees'])
    return bytes(d[:p['pool_len']])


def args(p):
    if p['payload'] is not None:
        return DISC + bytes.fromhex(p['payload'])
    fee = b'\x00' if p['fee'] is None else b'\x01' + struct.pack('<Q', p['fee'])
    return DISC + bytes(NAMED[p['cc']]) + bytes([1 if p['holder'] else 0]) + fee


def cases():
    out = []
    def c(name, **kw):
        p = dict(DEFAULT); p.update(kw); p['name'] = name; out.append(p)
    c('ok-no-fee')
    c('ok-fee-1', fee=1)
    c('ok-fee-max', fee=1000)
    c('fee-max-plus-1', fee=1001)
    c('fee-0', fee=0)
    c('fee-u64-max', fee=2**64 - 1, max_bps=2**64 - 1)
    c('fee-max-0', fee=1, max_bps=0)
    c('fee-not-configurable', fee=1, configurable=0)
    c('no-fee-not-configurable', configurable=0)
    c('fee-configurable-byte-2', fee=1, configurable=2)
    c('quote-wsol-fee', fee=1, quote='WSOL')
    c('quote-usdc-fee', fee=1, quote='USDC')
    c('quote-wsol-no-fee', quote='WSOL')
    c('quote-wsol-fee-0-not-configurable', fee=0, quote='WSOL', configurable=0)
    c('cashback-fee', fee=1, cashback=1)
    c('cashback-no-fee', cashback=1)
    c('cashback-holder-fee', fee=1, cashback=1, holder=True, cc='HR')
    c('holder-ok', holder=True, cc='HR')
    c('holder-wrong-cc', holder=True, cc='NEW_CC')
    c('holder-pool-to-holder', pool_holder=1, holder=True, cc='HR')
    c('holder-pool-to-normal', pool_holder=1, holder=False, cc='NEW_CC')
    c('holder-pool-to-normal-hr-key', pool_holder=1, holder=False, cc='HR')
    c('holder-pool-holder-wrong-cc', pool_holder=1, holder=True, cc='NEW_CC')
    c('holder-pool-byte-2', pool_holder=2, holder=True, cc='HR')
    c('non-canonical-creator', creator='OTHER')
    c('mayhem', mayhem=1)
    c('non-canonical-and-mayhem', creator='OTHER', mayhem=1)
    c('mayhem-and-holder-wrong', mayhem=1, holder=True, cc='NEW_CC')
    c('creator-fees-1', creator_fees=1)
    c('creator-fees-and-fee-oor', creator_fees=1, fee=1001)
    c('cc-arbitrary-key', cc='QUOTE', fee=None)
    c('can-edit-0', can_edit=0)
    c('pa-not-signer', pa_signer=False)
    c('pa-wrong-key', pa_key='OTHER')
    c('payload-empty', payload='')
    c('payload-no-option', payload=bytes(NEW_CC).hex() + '00')
    c('payload-option-tag-2', payload=bytes(NEW_CC).hex() + '0002')
    c('payload-bool-2', payload=bytes(NEW_CC).hex() + '0200')
    c('payload-fee-short', payload=bytes(NEW_CC).hex() + '000101')
    c('payload-trailing', payload=bytes(NEW_CC).hex() + '0000ff')
    c('config-bad-disc', config_disc_ok=False)
    c('config-len-940', config_len=940)
    c('config-len-941', config_len=941)
    c('pool-len-287', pool_len=287)
    c('pool-len-286', pool_len=286)
    c('pool-len-270', pool_len=270)
    return out


def run_case(p, image):
    vm = LiteSVM().with_sigverify(False).with_transaction_history(0)
    if isinstance(image, bytes):
        vm.add_program(PROGRAM, image)
    else:
        vm.add_program_from_file(PROGRAM, image)
    vm.set_clock(Clock(100, 1234567890, 0, 0, 1234567890))
    vm.airdrop(PAYER.pubkey(), 10**12)
    vm.set_account(EVENT, Account(10**9, b'', Pubkey.default()))
    vm.set_account(CONFIG, Account(10**9, global_config(p), PROGRAM))
    vm.set_account(POOL, Account(p['pool_lamports'], pool(p), PROGRAM))
    pa = NAMED[p['pa_key']]
    metas = [AccountMeta(PAYER.pubkey(), True, True), AccountMeta(CONFIG, False, False),
             AccountMeta(POOL, False, True), AccountMeta(pa, p['pa_signer'], False),
             AccountMeta(SYSTEM, False, False), AccountMeta(EVENT, False, False),
             AccountMeta(PROGRAM, False, False)]
    bh = vm.latest_blockhash()
    tx = Transaction.new_unsigned(Message.new_with_blockhash([Instruction(PROGRAM, args(p), metas)], PAYER.pubkey(), bh))
    tx.partial_sign([PAYER], bh)
    r = vm.send_transaction(tx)
    failed = isinstance(r, FailedTransactionMetadata)
    meta = r.meta() if failed else r
    cu = meta.compute_units_consumed
    cu = cu() if callable(cu) else cu
    a = vm.get_account(POOL)
    return {'error': str(r.err()) if failed else None, 'cu': cu, 'logs': list(meta.logs()),
            'state': {'pool': bytes(a.data).hex(), 'pool_lamports': a.lamports}}


def anchor_code(logs):
    for line in logs:
        if 'Error Code: ' in line:
            return line.split('Error Code: ')[1].split('.')[0]
        if 'panicked' in line:
            return 'panic'
    return None


def program_logs(logs):
    """Full log list without the per-program 'consumed N of M compute units' lines."""
    return [l for l in logs if not ('consumed' in l and 'compute units' in l)]


def observed(rec):
    d = bytes.fromhex(rec['state']['pool'])
    if len(d) < 287:
        return {'pool_len': len(d)}
    return {'pool_len': len(d), 'coin_creator_changed': d[211:243] != bytes(OLD_CC), 'is_cashback_coin': d[244],
            'creator_fee_bps': struct.unpack_from('<Q', d, 261)[0], 'can_edit_creator_fee': d[269],
            'is_holder_reward': d[270]}


PREFIX = b'programs/pump-amm/'


def elf_sections(blob):
    shoff, = struct.unpack_from('<Q', blob, 0x28)
    shentsize, shnum, shstrndx = struct.unpack_from('<HHH', blob, 0x3a)
    hs = [struct.unpack_from('<IIQQQQIIQQ', blob, shoff + i * shentsize) for i in range(shnum)]
    st = hs[shstrndx]; names = blob[st[4]:st[4] + st[5]]
    return {names[h[0]:names.index(b'\0', h[0])].decode(): (h[4], h[5]) for h in hs if h[0]}


def strip_prefix(blob):
    """Control image: the original with every reference to a 'programs/pump-amm/src/*.rs' string
    moved 18 bytes later (past the prefix) and the matching length immediate lowered by 18."""
    b = bytearray(blob)
    secs = elf_sections(bytes(b))
    ro_off, ro_len = secs['.rodata']; tx_off, tx_len = secs['.text']
    starts = {}
    for m in re.finditer(re.escape(PREFIX) + rb'src/[A-Za-z0-9_/]+\.rs', bytes(b[ro_off:ro_off + ro_len])):
        starts[ro_off + m.start()] = len(m.group(0))  # sh_addr == sh_offset for .rodata here
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


def produce(images):
    stripped, _ = strip_prefix(pathlib.Path(images['original']).read_bytes())
    rows = []
    for p in cases():
        rec = {'case': p['name'], 'params': {k: v for k, v in p.items() if k != 'name'}}
        if isinstance(p['fee'], int) and p['fee'] >= 2**53:
            rec['params']['fee'] = str(p['fee'])
        if p['max_bps'] >= 2**53:
            rec['params']['max_bps'] = str(p['max_bps'])
        for tag in ('original', 'candidate'):
            rec[tag] = run_case(p, images[tag])
        s = run_case(p, stripped)
        rec['stripped_original'] = {'cu': s['cu'], 'same_error_state_as_candidate': (s['error'], s['state']) == (rec['candidate']['error'], rec['candidate']['state']),
                                    'same_logs_as_candidate': s['logs'] == rec['candidate']['logs']}
        o, c = rec['original'], rec['candidate']
        norm = lambda logs: [l.replace('thrown in programs/pump-amm/src/', 'thrown in src/') for l in program_logs(logs)]
        rec['same_error'] = o['error'] == c['error']
        rec['same_state'] = o['state'] == c['state']
        rec['same_logs'] = o['logs'] == c['logs']
        rec['same_logs_ex_cu'] = program_logs(o['logs']) == program_logs(c['logs'])
        rec['same_logs_path_normalized'] = norm(o['logs']) == norm(c['logs'])
        rec['cu_delta'] = c['cu'] - o['cu']
        rec['anchor_error'] = {t: anchor_code(rec[t]['logs']) for t in ('original', 'candidate')}
        rec['error_site'] = {t: next((l.split('AnchorError ')[1].split('. Error Code')[0]
                                      for l in rec[t]['logs'] if l.startswith('Program log: AnchorError ')), None)
                             for t in ('original', 'candidate')}
        rec['observed'] = observed(o)
        rows.append(rec)
    return rows


def sha_file(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


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
    summary = {
        'image_sha256': {k: sha_file(v) for k, v in images.items()},
        'case_count': len(rows),
        'behavior_match': sum(r['same_error'] and r['same_state'] for r in rows),
        'log_match_exact': sum(r['same_logs'] for r in rows),
        'log_match_ex_cu': sum(r['same_logs_ex_cu'] for r in rows),
        'log_match_path_normalized': sum(r['same_logs_path_normalized'] for r in rows),
        'cu_equal': sum(r['cu_delta'] == 0 for r in rows),
        'cu_delta_histogram': {str(d): sum(r['cu_delta'] == d for r in rows) for d in sorted({r['cu_delta'] for r in rows})},
        'cases': [{'case': r['case'], 'error': r['original']['error'], 'anchor_error': r['anchor_error'],
                   'error_site': r['error_site'], 'cu_original': r['original']['cu'],
                   'cu_candidate': r['candidate']['cu'], 'cu_delta': r['cu_delta'],
                   'same_error': r['same_error'], 'same_state': r['same_state'],
                   'same_logs_path_normalized': r['same_logs_path_normalized'],
                   'observed': r['observed']} for r in rows],
        'receipts_sha256': hashlib.sha256(body).hexdigest(),
        'stripped_original_control': {
            'sites_patched': strip_prefix(pathlib.Path(images['original']).read_bytes())[1],
            'cu_equal_to_candidate': sum(r['stripped_original']['cu'] == r['candidate']['cu'] for r in rows),
            'logs_equal_to_candidate': sum(r['stripped_original']['same_logs_as_candidate'] for r in rows),
            'error_state_equal_to_candidate': sum(r['stripped_original']['same_error_state_as_candidate'] for r in rows),
        },
    }
    (out / 'report.json.gz').write_bytes(gzip.compress(json.dumps(summary, sort_keys=True, indent=1).encode(), mtime=0))
    print(json.dumps({k: summary[k] for k in ('case_count', 'behavior_match', 'log_match_exact', 'log_match_ex_cu',
                                              'log_match_path_normalized', 'cu_equal', 'cu_delta_histogram',
                                              'stripped_original_control')}))


if __name__ == '__main__':
    main()
