import sys,re,glob,os
d=sys.argv[1]; names=sys.argv[2].split(',')
fs=sorted(f for f in os.listdir(d) if re.match(r'pump_recovered\.buy_v2-buy_exact_quote_in_handler\.\d{3}-\d{3}\..*\.after\.mir$',f))
for f in fs:
    s=open(os.path.join(d,f)).read()
    out=[]
    for n in names:
        ls=re.findall(r'debug '+n+r' => (_\d+);',s)
        r=[]
        for l in ls:
            r.append(f"{l}:{'L' if f'StorageLive({l})' in s else '-'}")
        out.append(n+'['+' '.join(r)+']')
    print(f.split('handler.')[1][:40].ljust(40),' '.join(out))
