#!/bin/bash
# runpair.sh n1 n2 ... : run trials two at a time (slots 0/1), append to tmp/results.txt
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a134-cto-headroute306; cd $O
a=("$@"); i=0
while [ $i -lt ${#a[@]} ]; do
  bash tools/trial.sh ${a[$i]} 0 >> tmp/results.txt 2>&1 &
  [ -n "${a[$((i+1))]}" ] && bash tools/trial.sh ${a[$((i+1))]} 1 >> tmp/results.txt 2>&1 &
  wait; i=$((i+2))
  rm -rf var/*
done
echo DONE >> tmp/results.txt
