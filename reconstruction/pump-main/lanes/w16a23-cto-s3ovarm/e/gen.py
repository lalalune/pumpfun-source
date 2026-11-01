#!/usr/bin/env python3
"""gen.py: OV-on-S3n edit sets. Each cell = S3n edits + OV edits, applied in order to main's admin_cto.rs
(each old string must occur exactly once in the text at that point; line count kept). Writes e/<cell>.py."""
import json, runpy, sys
O = '/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a23-cto-s3ovarm'
WT = '/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a23-cto-s3ovarm'
S3N = [tuple(x) for x in runpy.run_path(O + '/e/S3n.py')['EDITS']]

SIG = 'holder_key:&Pubkey,sharing:&Pubkey,hf:&mut bool)->Result<Pubkey>{'
HARM = '*hf=true;*holder_key}else{'
NEND = 'if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}*hf=false;t};'
OKT = ' Ok(target)}pub fn execute('
CALL = 'let mut hf=false;let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,&mut hf)?;'
SUD = 'let mut sharing_update:Option<Option<Pubkey>>=None;'
TREE = ('let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);'
        'target=a.bonding_curve.creator;(false,true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};')
TUP = '(hf,cashback,target,sharing_update,collect_old,skip)};'
ARGS = 'let args=&(new,);'
RS = ('sharing_config_reset:sharing_update.is_some()', 'sharing_config_reset:shared')
ELSE = '{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};'

V = {}
# --- A: target override inside validate's non-holder arm (w15a20 ov1/ov1a/ov1b) ---
sig_sh = (SIG, SIG.replace('hf:&mut bool)', 'hf:&mut bool,shared:bool)'))
call_sh = (CALL, CALL.replace('&mut hf)?;', '&mut hf,shared)?;'))
V['A1'] = [sig_sh, (NEND, NEND.replace('*hf=false;t};', '*hf=false;if shared{st.creator}else{t}};')), call_sh]           # ov1a
V['A0'] = V['A1'] + [('target=a.bonding_curve.creator;(false,true)', '(false,true)'),
                     ('let mut hf=false;let mut target=validate(', 'let mut hf=false;let target=validate(')]            # ov1
V['A2'] = [sig_sh, (NEND, NEND.replace('*hf=false;t};', '*hf=false;if !shared{t}else{st.creator}};')), call_sh]          # ov1b
V['A3'] = [sig_sh, (NEND, NEND.replace('*hf=false;t};', 'if shared{*hf=false;st.creator}else{*hf=false;t}};')), call_sh]  # hf per sub-arm
FWD = [('sharing_update=Some(args.0);', 'sharing_update=Some(new);'), (ARGS, '')]
V['A1f'] = V['A1'] + FWD
V['A0f'] = V['A0'] + FWD
V['A1r'] = V['A1'] + [RS]
V['A0r'] = V['A0'] + [RS]
# --- B: sharing tag out-param su written per arm inside validate ---
sig_su = (SIG, SIG.replace('hf:&mut bool)', 'hf:&mut bool,shared:bool,su:&mut Option<Option<Pubkey>>)'))
call_su = (CALL + SUD, 'let mut hf=false;let mut su=None;let target=validate(&st,hopt,fee,new,&holder_key,&sk,&mut hf,shared,&mut su)?;')
tree_b = (TREE, 'let (collect_old,skip)=if shared{if holder{(false,false)}else{(false,true)}}else' + ELSE)
tup_b = (TUP, '(hf,cashback,target,su,collect_old,skip)};')
V['B1'] = [sig_su, (HARM, '*hf=true;if shared{*su=Some(None);}*holder_key}else{'),
           (NEND, NEND.replace('*hf=false;t};', '*hf=false;if shared{*su=Some(new);st.creator}else{t}};')),
           call_su, tree_b, tup_b, (ARGS, '')]
V['B2'] = [sig_su, (HARM, '*hf=true;*su=if shared{Some(None)}else{None};*holder_key}else{'),
           (NEND, NEND.replace('*hf=false;t};', '*hf=false;if shared{*su=Some(new);st.creator}else{*su=None;t}};')),
           call_su, tree_b, tup_b, (ARGS, '')]
V['B3'] = [sig_su, (HARM, '*hf=true;if shared{*su=Some(None);}*holder_key}else{'),
           (NEND, NEND.replace('*hf=false;t};', '*hf=false;if shared{*su=Some(new);st.creator}else{t}};')),
           (CALL + SUD, 'let mut hf=false;let mut su=None;let target=validate(&st,hopt,fee,args.0,&holder_key,&sk,&mut hf,shared,&mut su)?;'),
           tree_b, tup_b]                                                                    # keeps args: new passed as args.0
V['B1r'] = V['B1'] + [RS]
V['B2r'] = V['B2'] + [RS]
# B6: su written in validate's non-holder arm only; holder shared Some(None) stays in execute's tree
V['B6'] = [sig_su, (NEND, NEND.replace('*hf=false;t};', '*hf=false;if shared{*su=Some(new);st.creator}else{t}};')),
           call_su, (TREE, 'let (collect_old,skip)=if shared{if holder{su=Some(None);(false,false)}else{(false,true)}}else' + ELSE),
           tup_b, (ARGS, '')]
V['B6r'] = V['B6'] + [RS]
# --- C: ov2-style, validate returns (target,su,collect_old,skip) ---
V['C1'] = [(SIG + 'let holder=hopt==Some(true);',
            'holder_key:&Pubkey,sharing:&Pubkey,hf:&mut bool,shared:bool)->Result<(Pubkey,Option<Option<Pubkey>>,bool,bool)>{let holder=hopt==Some(true);'),
           (' let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*hf=true;*holder_key}else{',
            ' let (target,su,co,skip)=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*hf=true;if shared{(*holder_key,Some(None),false,false)}else{(*holder_key,None,!st.holder_reward&&st.creator!=Pubkey::default(),true)}}else{'),
           (NEND, NEND.replace('*hf=false;t};', '*hf=false;if shared{(st.creator,Some(new),false,true)}else{(t,None,!st.holder_reward&&st.creator!=Pubkey::default(),true)}};')),
           (OKT, ' Ok((target,su,co,skip))}pub fn execute('),
           (CALL + SUD + TREE, 'let mut hf=false;let (target,sharing_update,collect_old,skip)=validate(&st,hopt,fee,new,&holder_key,&sk,&mut hf,shared)?;'),
           (ARGS, '')]
# --- D: w14a89 vba/vbb: target out-param, validate -> Result<()> ---
V['D1'] = [(SIG + 'let holder=hopt==Some(true);',
            'holder_key:&Pubkey,sharing:&Pubkey,hf:&mut bool,hb:bool,shared:bool,out:&mut Pubkey)->Result<()>{let holder=hopt==Some(true);'),
           (' let target=if holder{', ' *out=if hb{'),
           (NEND, NEND.replace('*hf=false;t};', '*hf=false;if shared{st.creator}else{t}};')),
           (OKT, ' Ok(())}pub fn execute('),
           (CALL, 'let mut hf=false;let mut target=Pubkey::default();validate(&st,hopt,fee,new,&holder_key,&sk,&mut hf,holder,shared,&mut target)?;'),
           ('target=a.bonding_curve.creator;(false,true)', '(false,true)')]
V['D2'] = V['D1'][:-1]                                                                          # keeps execute override

if __name__ == '__main__':
    base = open(WT + '/programs/pump/src/creator/admin_cto.rs').read()
    only = sys.argv[1:]
    for k, v in V.items():
        if only and k not in only: continue
        s = base; n0 = s.count('\n'); E = S3N + v
        for a, b in E:
            c = s.count(a); assert c == 1, (k, c, a[:120]); s = s.replace(a, b)
        assert s.count('\n') == n0, (k, 'lines')
        open(f'{O}/e/{k}.py', 'w').write('EDITS=' + json.dumps(E) + '\n')
        open(f'{O}/e/{k}.rs', 'w').write(s)
        print(k, len(E), 'ok')
