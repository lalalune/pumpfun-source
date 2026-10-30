import sys,re; sys.path.insert(0,__import__('os').path.dirname(__file__)); import iredit
mod=open(sys.argv[1]).read(); _,fn,_=iredit.split_fn(mod)
al=re.findall(r'^\s*%(\S+) = alloca (.*?), align',fn,re.M)
lt=set(re.findall(r'lifetime\.start\.p0\(i64 \d+, ptr (?:nonnull )?%(\S+)\)',fn))
pat=sys.argv[2] if len(sys.argv)>2 else None
print(' '.join(f"{a}{'*' if a in lt else ''}:{t.replace(' x i8','').replace('[','').replace(']','')}" for a,t in al))
