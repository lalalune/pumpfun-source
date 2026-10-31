import sys
f=sys.argv[1]; t=open(f).read()
anchor="  // Sort them by weight.\n  llvm::stable_sort(SSIntervals, IntervalSorter());\n\n  NextColors.resize(AllColors.size());"
assert t.count(anchor)==1
hook='''  // lane w15a32 experiment hook (private llc only): SSC_WSET="ss:=w,ss:+d" sets or offsets spill-slot interval weights
  if (const char *E = getenv("SSC_WSET")) {
    std::string S(E); size_t p = 0;
    while (p < S.size()) {
      size_t c = S.find(',', p); if (c == std::string::npos) c = S.size();
      std::string tok = S.substr(p, c - p); p = c + 1;
      size_t k = tok.find(':'); if (k == std::string::npos || k + 2 > tok.size()) continue;
      int ss = atoi(tok.substr(0, k).c_str()); char op = tok[k + 1];
      float w = (float)atof(tok.c_str() + k + 2);
      for (LiveInterval *li : SSIntervals)
        if (Register::stackSlot2Index(li->reg()) == ss)
          li->setWeight(op == '+' ? li->weight() + w : w);
    }
  }
'''
t=t.replace(anchor,hook+anchor)
t=t.replace('#include <vector>\n','#include <vector>\n#include <cstdlib>\n#include <string>\n',1)
open(f,'w').write(t)
