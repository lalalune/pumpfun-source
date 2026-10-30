#!/usr/bin/env python3
"""Read-only verification of pinned dependency-path compiler outputs.

Requires this script and the sibling mpl-producer/verify_mpl.py and
borsh-producer/verify_producer.py. Artifacts are supplied separately by an
explicit JSON object mapping each PINS key below to an absolute local path.
"""
import argparse
import importlib.util
import json
from pathlib import Path

helper = Path(__file__).resolve().parent.parent / 'mpl-producer' / 'verify_mpl.py'
spec = importlib.util.spec_from_file_location('producer_helpers', helper)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
require, sha, differences, sections = m.require, m.sha, m.differences, m.sections
PINS = {'control': '8d9c35696664888ec05c42de2e81f40d9ef79284839f32b090aae36df570c88c', 'prior': '3eb5a1e655ed741aa9ad8fb6ab54940834dbbc5e9f8b5abf3d81ecfb18e4f20e', 'candidate': '2838d90f7e6d15904f9d3727746fa020c23e6248568ccbaa91badc14befc379b', 'repeat': '2838d90f7e6d15904f9d3727746fa020c23e6248568ccbaa91badc14befc379b', 'original': '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d', 'spl_token_control': '0cb8d94cdecf01a3aa8cadd9e1920dd8710da464f030209e9541ade5a24747fe', 'spl_token_candidate': '8a6180d9dfa96b3c6bffe8a5b96465eaa6b0ce3ee6a4c9f076f27e80453c467a', 'spl_token_repeat': '8a6180d9dfa96b3c6bffe8a5b96465eaa6b0ce3ee6a4c9f076f27e80453c467a', 'spl_token_2022_control': 'deecc38549c9d94898fdcebabb630eea9f1c56af02d7185add0df133ea5f6861', 'spl_token_2022_candidate': '9a18cac91d18412fda334cc08bd06c4ee64b1e5d9c402a72db828f73577b67f0', 'spl_token_2022_repeat': '9a18cac91d18412fda334cc08bd06c4ee64b1e5d9c402a72db828f73577b67f0', 'spl_token_metadata_interface_control': '9f6480ec542cb664d5f163b1787fa1908022848d091d67ad6a9a640f1a2fa8f9', 'spl_token_metadata_interface_candidate': '72686546666811f14d4e8e0d648c94e09343a18c12ddaedd3fb23c461bf37783', 'spl_token_metadata_interface_repeat': '72686546666811f14d4e8e0d648c94e09343a18c12ddaedd3fb23c461bf37783', 'anchor_lang_control': '4ef13175ee9425e0c60f4c15d1d6e8a35e177d7923aa0a18eb7022e27eac4fa1', 'anchor_lang_candidate': 'fd7ce8d2e8e1b4e211cf0a2e17fd0b5af1a64c05187a343c651542248cdb725e', 'anchor_lang_repeat': 'fd7ce8d2e8e1b4e211cf0a2e17fd0b5af1a64c05187a343c651542248cdb725e', 'solana_borsh_control': '72660343eeac29be8c4b9e659ddb626876dfce333b105b2feaf343e625d71f8b', 'solana_borsh_candidate': '0a0e740144241275f12e1f06c5ab0f6efdcae74789a37babe635270b67a4de23', 'solana_borsh_repeat': '0a0e740144241275f12e1f06c5ab0f6efdcae74789a37babe635270b67a4de23', 'bincode_control': 'dd92307162b992ce70acb0b21c44bba19ae16a5f7a6741c7a388c30d22e5ce4b', 'bincode_candidate': 'f68da424ebcbef4e1fab9563bbcac9fe57f11bef9e9ad1b1675b6668be81a176', 'bincode_repeat': 'f68da424ebcbef4e1fab9563bbcac9fe57f11bef9e9ad1b1675b6668be81a176', 'bs58_control': '9a695ce7b9800ac3a6b5a2b15a0b088ad9b3ff97836e01caf141fcf679b715fe', 'bs58_candidate': '1d07bae0119f0e35749f25aafb006808f433d3858cca00512abee17f5ef97ae5', 'bs58_repeat': '1d07bae0119f0e35749f25aafb006808f433d3858cca00512abee17f5ef97ae5'}
OFFSETS = [1421, 1424, 17799, 17802, 18143, 18153, 18166, 18419, 18429, 18442, 18639, 18739, 18861, 19593, 19610, 25291, 27142]
MEMBER_COUNTS = {'spl_token': 4, 'spl_token_2022': 6,
                 'spl_token_metadata_interface': 2, 'anchor_lang': 4,
                 'solana_borsh': 2, 'bincode': 4, 'bs58': 2}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--inputs', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    paths = json.loads(args.inputs.read_text(encoding='utf-8'))
    require(set(paths) == set(PINS), 'Unexpected input keys')
    require(all(Path(p).is_absolute() for p in paths.values()), 'Use absolute paths')
    raw = {k: Path(p).read_bytes() for k, p in paths.items()}
    require(all(sha(raw[k]) == pin for k, pin in PINS.items()), 'Input SHA-256 mismatch')
    require(raw['candidate'] == raw['repeat'], 'Root repeat differs')
    c = sections(raw['control']); original = sections(raw['original'])['.rodata']['raw']
    stages = {}
    for name, count, remaining in [('control', 0, 104), ('prior', 7, 97), ('candidate', 17, 87)]:
        s = sections(raw[name]); changes = differences(raw['control'], raw[name])
        expected = [(c['.rodata']['offset'] + off, 92, 47) for off in OFFSETS[:count]]
        require(changes == expected, 'Unexpected whole-image changes')
        require(s['.text'] == c['.text'] and s['.data.rel.ro'] == c['.data.rel.ro'], 'Code or relocated data changed')
        require(len(differences(original, s['.rodata']['raw'])) == remaining, 'Unexpected residual')
        require(all(original[off] == s['.rodata']['raw'][off] == 47 for off in OFFSETS[:count]), 'Changed byte differs from original')
        stages[name] = {'sha256': sha(raw[name]), 'bytes': len(raw[name]),
                        'whole_image_changes': changes, 'original_rodata_differences': remaining}
    archives = {}
    for crate, count in MEMBER_COUNTS.items():
        a, b, repeat = [raw[crate + '_' + key] for key in ['control', 'candidate', 'repeat']]
        require(b == repeat, 'Dependency repeat differs')
        am, bm = m.members(a), m.members(b)
        require(am.keys() == bm.keys(), 'Archive members changed')
        changes = differences(a, b)
        require(len(changes) == count and all(x == 92 and y == 47 for _, x, y in changes), 'Unexpected library changes')
        members = {key: differences(am[key], bm[key]) for key in am}
        require(sum(len(v) for v in members.values()) == count, 'Archive headers changed')
        archives[crate] = members
    report = {'result': 'PASS', 'source_revision': '3bbbe91e881df9ff617ecb5392ecb0559a7691c0',
              'pins': PINS, 'stages': stages, 'archive_changes': archives,
              'independent_repeats_equal': True,
              'scope': 'Seventeen section-relative raw data corrections, ten beyond the prior producer chain. No formatter-gap closure, function-window gain, native qualification, whole-original identity or runtime claim.'}
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'result': 'PASS', 'corrected': 17, 'additional': 10, 'remaining_rodata_differences': 87}))


if __name__ == '__main__':
    main()
