import sys,re
p=sys.argv[1]; s=open(p).read()
# 1) config fields
s=s.replace("  unsigned FirstNew = ~0u;\n};","  unsigned FirstNew = ~0u;\n  std::map<unsigned, std::string> CascS, WeightS;\n  std::set<unsigned> CascDone;\n};",1)
s=s.replace('  rpParse(getenv("RAPRIO_HINT"), RP.HintS);','  rpParse(getenv("RAPRIO_HINT"), RP.HintS);\n  rpParse(getenv("RAPRIO_CASC"), RP.CascS);\n  rpParse(getenv("RAPRIO_WEIGHT"), RP.WeightS);',1)
# 2) cascade at enqueue
anchor="  unsigned Ret = PriorityAdvisor->getPriority(*LI);\n"
assert anchor in s
s=s.replace(anchor,"""  {
    unsigned Ic = Register::virtReg2Index(Reg);
    auto Itc = RP.CascS.find(Ic);
    if (Itc != RP.CascS.end() && !RP.CascDone.count(Ic)) {
      RP.CascDone.insert(Ic);
      ExtraInfo->setCascade(Reg, (unsigned)std::stoul(Itc->second, nullptr, 0));
      if (RP.Log) *RP.Log << "C " << Ic << " " << Itc->second << "\\n";
    }
  }
"""+anchor,1)
# 3) weights after calculateSpillWeightsAndHints (inside the RAPRIO init block)
a2="  if (RP.Log) *RP.Log << \"FN \" << MF->getName() << \"\\n\";"
assert a2 in s
s=s.replace(a2,"""  RP.CascDone.clear();
  for (auto &KV : RP.WeightS) {
    if (KV.first >= MRI->getNumVirtRegs()) continue;
    Register R = Register::index2VirtReg(KV.first);
    if (!LIS->hasInterval(R)) continue;
    LiveInterval &LIw = LIS->getInterval(R);
    const std::string &V = KV.second;
    float W = (!V.empty() && V[0] == '*') ? LIw.weight() * std::stof(V.substr(1)) : std::stof(V);
    LIw.setWeight(W);
  }
"""+a2,1)
open(p,'w').write(s)
s=open(p).read()
old='(VRM->getStackSlot(R) != VirtRegMap::NO_STACK_SLOT ? "stack" : "-")'
assert old in s
s=s.replace(old,'(VRM->getStackSlot(R) != VirtRegMap::NO_STACK_SLOT ? ("fi" + std::to_string(VRM->getStackSlot(R))) : std::string("-"))')
s=s.replace('*RP.Log << "A " << I << " " << (VRM->hasPhys(R) ? TRI->getName(VRM->getPhys(R)) :','*RP.Log << "A " << I << " " << (VRM->hasPhys(R) ? std::string(TRI->getName(VRM->getPhys(R))) :')
open(p,'w').write(s)
s=open(p).read()
old='    if (RP.Log) *RP.Log << "S " << Register::virtReg2Index(VirtReg.reg()) << "\\n";\n    spiller().spill(LRE);\n'
assert old in s, 'S anchor'
s=s.replace(old,old+'    if (RP.Log) { Register Og = VRM->getOriginal(VirtReg.reg()); *RP.Log << "SF " << Register::virtReg2Index(VirtReg.reg()) << " orig " << Register::virtReg2Index(Og) << " fi " << VRM->getStackSlot(Og) << "\\n"; }\n',1)
open(p,'w').write(s)
