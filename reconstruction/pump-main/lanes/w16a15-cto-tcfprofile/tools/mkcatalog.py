#!/usr/bin/env python3
"""mkcatalog.py <catalog.json> <out sizeknobs json> [pairs.jsonl ...]: write the region-tagged size-knob catalog in the
w12a13 sizeknobs-cto.json shape (knobs[].results.<base>) plus the splice-priced composite table. Experiment only."""
import sys,os,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import genes_fk
cat=json.load(open(sys.argv[1])); out=sys.argv[2]
LIBS={'w15a03-cto-stitch15':'origin/swarm/w15a03-cto-stitch15:reconstruction/pump-main/lanes/w15a03-cto-stitch15/tools/genes_s15.py (gene names joined by +)',
      'w15a13-cto-jointraceback':'origin/swarm/w15a13-cto-jointraceback:reconstruction/pump-main/lanes/w15a13-cto-jointraceback/e/<name>.py',
      'w15a16-cto-mpermrank':'origin/swarm/w15a16-cto-mpermrank tools/genes_mp.py',
      'w15a30-cto-litfamily':'origin/swarm/w15a30-cto-litfamily tools/lit.py (key:order = struct-literal field permutation)',
      'w15a01-cto-devolfill':'origin/swarm/w15a01-cto-devolfill genes',
      'w16a07-cto-sweeptuple':'$C/lanes/w16a07-cto-sweeptuple/e/<name>.py (PR #3859)',
      'w16a02-cto-faithknobs':'tools/genes_fk.py in this lane'}
knobs=[]
for d in cat:
    if d['M']<int(os.environ.get('MIN_M','2150')): continue
    k={'name':d['name'],'lane':d['lane'],'genes':d['genes'],'gene_library':LIBS.get(d['lane'],d['lane']),
       'results':{'main9bd38c7':{'bytes':d['bytes'],'delta_bytes':d['delta_bytes'],'M':d['M'],'dM':d['dM'],'ratio':d['ratio'],
                                 'delta_ratio':round(d['ratio']-0.67376,5),'identical_to_base':d['identical_to_main'],
                                 'by_region':d.get('by_region'),'changes':d.get('changes'),'jumps_bad':d.get('jumps_bad'),
                                 'jumps_aligned':d.get('jumps_aligned'),'rfj_lcs':d.get('rfj_lcs'),'drift_med':d.get('drift_med')}}}
    if d['lane']=='w16a02-cto-faithknobs':
        try: k['edit']=[{'old':e[0],'new':e[1]} for g in d['genes'].split('+') for e in genes_fk.G[g] if not callable(e)]
        except Exception: pass
    knobs.append(k)
comp=[]
for f in sys.argv[3:]:
    for l in open(f):
        r=json.loads(l)
        if r['M']>=2246: comp.append({'source':os.path.basename(f),**r})
comp.sort(key=lambda r:-r['M'])
json.dump({'lane':'w16a02-cto-faithknobs','target':'0x22a10 admin_cto::execute (programs/pump/src/creator/admin_cto.rs)','pinned_bytes':27400,
  'bases':{'main9bd38c7':{'commit':'9bd38c7d5','bytes':27400,'ratio':0.67376,'M':2249,'slots':3124,'rfj_lcs':3002,'jumps_bad':113,'jumps_aligned':261,
           'note':'admin_cto source identical to 86e2a6b/9120883/1cc4879; the raw-IR capture of main equals w15a03 n0, w15a13 M0, w15a16 n0'}},
  'how_to_read':('Every knob is a cached raw-IR oracle capture (capraw + opt -O3 + llc, = measure.sh) of a SOURCE variant on the current '
    'admin_cto source; bytes and M are re-derived from its fn.bin. by_region/changes say where the byte delta lands, by call-anchor '
    'alignment against main (regions: E entry <0x3a8, V validate+tree <0x1a88, SH sweep head <0x26b8, TC TCF clones/call/Rent <0x3c40, '
    'SC sharing-CPI build <0x4a28, PC post-CPI pool/event <0x5490, ER error blocks <0x5990, NA sweep native arm <0x5bc0, WA wallet + '
    'sweep token-arm CPI <0x6a68, TL tail; offsets are main candidate offsets). jumps_bad/jumps_aligned/rfj_lcs/drift_med are the '
    'w16-strategy decomp.py --drift metrics (main: 113/261/3002; drift entry -22, validate_tail -21, sharecpi -12, event_err -6). '
    'Sizes are not additive: use tools/splice.py (v2) to price composites (88/89 built multi-gene composites byte-identical), '
    'then build. composites[]: splice-priced sets with predicted M >= 2246; source pairs4.jsonl = zero-sum pairs on main 9bd38c7, '
    'lead_HevA6b.jsonl = ev6+A6 (now main 1f4e396, M 2251) plus the listed 0 B item or zero-sum pair.'),
  'knobs':knobs,'composites':comp[:400]},open(out,'w'),separators=(',',':'))
# one knob / composite per line for diffs and grep
t=open(out).read().replace('{"name":','\n{"name":').replace('{"source":','\n{"source":')
open(out,'w').write(t)
print(len(knobs),'knobs',len(comp),'composites')
