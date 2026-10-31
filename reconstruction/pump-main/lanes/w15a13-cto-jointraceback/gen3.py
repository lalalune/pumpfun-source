import runpy,itertools
C=runpy.run_path('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a118-cto-chunkrw15/e/common.py')
G=runpy.run_path('gen.py') if False else None
SU='let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};(holder,cashback,target,sharing_update,collect_old,skip)};'
SW='swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);'
P={
 'pa4':[(SU,'let mut sharing_update:Option<Option<Pubkey>>=None;let mut collect_old=false;let skip=if shared{if holder{sharing_update=Some(None);false}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;true}}else{collect_old=!st.holder_reward&&st.creator!=Pubkey::default();true};(holder,cashback,target,sharing_update,collect_old,skip)};')],
 'pa1':[(SU,'let mut sharing_update:Option<Option<Pubkey>>=None;let (skip,collect_old)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(true,false)}}else{(true,!st.holder_reward&&st.creator!=Pubkey::default())};(holder,cashback,target,sharing_update,collect_old,skip)};')],
 'pg3':[(SW,'swept=if skip{0}else{sweep(&ctx,&holder_key)?};')],
 'pg9':[(SW,'swept=if skip{Ok(0)}else{sweep(&ctx,&holder_key)}?;')],
 'pc9':[(SW,'swept=match skip{true=>0,false=>sweep(&ctx,&holder_key)?};')],
}
S={
 'snt':[(C['NT_OLD'],C['NT_PLAIN'])],
 'stok':[(C['TOK_OLD'],C['TOK_PLAIN'])],
 'stok2':[(C['TOK2_OLD'],C['TOK2_PLAIN'])],
 'sn3':[(C['NMIN_OLD'],C['NMIN_N3'])],
 'samm':[(C['AMM_OLD'],C['AMM_IF'])],
 'sdest':[(C['DEST_OLD'],C['DEST_RK'])],
 'snvd':[(C['NV_OLD'],C['NV_NONE']),(C['NV_AFTERDEST_OLD'],C['NV_AFTERDEST_NEW'])],
 'swg':[(C['WG_OLD'],C['WG_NEW'])],
 'swo':[(C['WO_OLD'],C['WO_NEW'])],
 'ssw1':[(C['SW1_OLD'],C['SW1_NEW']),(C['SW2_OLD'],C['SW2_NEW'])],
 'scoin':[(C['COIN_OLD'],C['COIN_DO'])],
}
names=[]
for p,pe in P.items():
    names.append(p); open(f'e/{p}.py','w').write(f'EDITS={pe!r}\nHYP={("skip-polarity form "+p)!r}\n')
for p,pe in P.items():
    for s,se in S.items():
        if p.startswith('pg') or p=='pc9':
            if s=='ssw1': 
                se=[(C['SW1_OLD'],C['SW1_NEW']),(pe[0][1],'let '+pe[0][1])]; ed=se+[pe[0]]
                ed=[(C['SW1_OLD'],C['SW1_NEW']),(pe[0][0],'let '+pe[0][1])]
            else: ed=pe+se
        else: ed=pe+se
        n=f'{p}_{s}'; names.append(n)
        open(f'e/{n}.py','w').write(f'EDITS={ed!r}\nHYP={("skip-polarity form "+p+" x sweep/tail form "+s)!r}\n')
open('list3','w').write(' '.join(names)); print(len(names))
