import sys,subprocess,re,os
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
syms=['h0333b338da31ddca','hc7eb8f545b1bbf09','hce86dbee7e23dfa8','h4559e188727ffbdf','hdf06088e8216d91c','h8b29659473c3c701','h5cebf789a726af6b']
for so in sys.argv[1:]:
    rd=subprocess.run([SDK+'/llvm-readelf','-sW',so],capture_output=True,text=True).stdout
    bq=[l.split() for l in rd.splitlines() if 'trade15buy_exact_quote17h' in l][0][1]
    print(so.split('/')[-2],'buy_exact_quote at',bq)
    for h in syms:
        m=[l.split() for l in rd.splitlines() if h in l]
        if not m: continue
        a=int(m[0][1],16)
        d=subprocess.run([SDK+'/llvm-objdump','-d','--no-show-raw-insn',f'--start-address={a:#x}',f'--stop-address={a+24:#x}',so],capture_output=True,text=True).stdout
        c=re.search(r'call (-?0x[0-9a-f]+|-?\d+)',d)
        print(f'  {h} at {a:#x} call imm {c.group(1) if c else None}')
