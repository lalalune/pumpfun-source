#!/usr/bin/env python3
"""mksummary.py: write SUMMARY.json for this lane from the result files (experiment bookkeeping)."""
import json,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a02-cto-faithknobs')
L=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows=[]
for f in ('res-9bd38c7.jsonl','res-1f4e396.jsonl'):
    for l in open(f'{O}/{f}'):
        r=json.loads(l); r['base']=f[4:11]; rows.append(r)
att={r['name']:{'base':r['base'],'genes':r.get('genes'),'bytes':r.get('bytes'),'M':r.get('M'),'ratio':r.get('ratio'),'error':r.get('error','')[:80] or None} for r in rows}
S={
 'lane':'w16a02-cto-faithknobs',
 'target':'0x22a10 admin_cto::execute (programs/pump/src/creator/admin_cto.rs), pinned 27,400 B',
 'bases':['9bd38c7 (0.67376, M 2249, 3124 slots)','1f4e396 (#3859 A6+ev6 landed by w16a07: 0.67436, M 2251, 3141 slots)'],
 'result':'notes and tools; no landing of my own. The exhaustive splice screen ranks w15a30 ev:6012345789abc + w16a07 m_A6 first; built here as H_ev6_A6 = M 2251 (0.67436) at 27,400 B, identical to w16a07 PR #3859 (found independently, landed by that lane). Nothing in the cached library improves on it.',
 'pr':3858,
 'best_zero_loss':{'variant':'H_ev6_A6 (= main 1f4e396 / #3859)','ratio':0.67436,'M':2251,'bytes':27400,'note':'oracle; measure.sh numbers are w16a07s (3141 slots, 1034/1034, 0 losses, differential ok)'},
 'ledger':'approach faithknob, keys 0x22a10-w16-{9bd38c7,1f4e396}-faithknob-<name>-v1',
 'findings':[
  'call-order map: orig vs main callee order differs at exactly 4 sites: entry PDA-first (#0-3), validate error blocks (#20-29), sweep token arm token_raw_amount before token_frozen (#53/54 = a1), pool gate owner memcmp before data_is_empty (#73/74)',
  'polarity map: main had exactly two -8 B ? polarity sites (line 660 -> A6, now on main; sharing CPI -> sh_iflet); no third',
  'sh_iflet -5 M is jump displacement only: one junk slot in the sweep head restores 7 displacements crossing the sharing CPI',
  'on 1f4e396 the sh_iflet pay band is cand 0x5448-0x5578 (+1) and 0x54b8 (+2): Clock::get()? / emit_cpi Err paths and event-authority drop glue; the original has mov64 r9,r1 there (Err payload via r1 into r9)',
  'splice oracle v2 reproduces 88/89 cached multi-gene builds byte for byte and ev6+A6 from its parts',
  'ST1 = sh_iflet+a1+tsplit lands at 27400 with +4 rfj (most faithful token-arm skeleton) but M -4',
  'deferred init of holder_key is load-bearing: let holder_key=PDA.0 (or let (holder_key,_)=) collapses to M 1869 at 0 B'],
 'screens':{'pairs_main_v2':'542 zero-sum pairs, best 2251 ev6+A6, 2250 ev6+sh_iflet / ev6+A1','on_ev6A6_v2':'2170 composites, none above 2251','shif_plus8_zero_on_new_main':'1456 composites, max 2250','triples_v1':'1251, max 2249'},
 'attempts':att,
 'rejected':['sweep-head spellings on sh_iflet (d_ctxkey, d_errinto, d_infokey, ap_info fold; v_direct -4; d_full/d_defer collapse; d_progid +96 B)','emit_cpi hand expansion (E1/E3) folds to the macro','ev double moves (6701..., 7601...) collapse','tsplit on frozen-first main collapses','T1/ST1 family -4..-6'],
 'unresolved_residuals':['sh_iflet needs +8 B of real code in the event Err paths on 1f4e396 (orig mov64 r9,r1: error-return payload register r9 vs ours r8)','token-arm r6/r8 naming blocks a1/T1 (w14a70 +5 bound)'],
 'next_ideas':['move the function error-return payload register from r8 to r9 (RA): would add the original mov64 r9,r1 in the sh_iflet pay band','price every new capture with tools/splice.py against the catalog before building (exact for local changes)','ST1 as a faithful base if the token-arm naming lever is found'],
 'catalog':'data/sizeknobs-w16.json (region-tagged, drift metrics, splice-priced composites)',
}
json.dump(S,open(f'{L}/SUMMARY.json','w'),indent=1)
print('ok',len(att))
