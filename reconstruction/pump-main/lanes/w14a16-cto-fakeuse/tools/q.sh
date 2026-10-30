#!/bin/bash
# q.sh <W> <listfile>: run "name<TAB>editfile<TAB>env" lines through capvar on work$W, append results to res.jsonl
cd ~/.cache/pumpfun-reconstruction/lanes/w14a16-cto-fakeuse
while IFS=$'\t' read -r n e envs; do
  [ -z "$n" ] && continue
  r=$(env $envs tools/capvar.sh $n $e $1 2>/dev/null | tail -1)
  echo "{\"trial\":\"$n\",\"edit\":\"$e\",\"env\":\"$envs\",\"res\":${r:-null}}" >> res.jsonl
  rm -rf var/$n rx/$n/m.o rx/$n/fn.bin
done < $2
