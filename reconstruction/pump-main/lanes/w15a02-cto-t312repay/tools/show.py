import re,sys
for f in sys.argv[1:]:
  for l in open(f):
    n=l.split()[0]
    m=re.search(r'B (\d+) M (\d+) fM (\d+) rM (\d+) rfM (\d+) rfjM (\d+)',l); r=re.search(r'"ratio": ([0-9.]+)',l)
    o=re.search(r'(284[IO] .*?) orig',l); eq='"eq_main": true' in l
    print('%-16s'%n, ' '.join(m.groups()) if m else l[:150].strip(), r.group(1) if r else '', 'EQMAIN' if eq else '', (o.group(1).replace('I ','').replace('O ','o ') if o else ''))
