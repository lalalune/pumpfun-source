"""Deterministic input tuples shared by the direct Pump trade validators.

These are the input values used by pump_validate_constant_product.py. They do
not contain historical outcomes or stand in for execution of the captured ELF.
"""
import random

def input_cases(base,quote):
    rng=random.Random(773104)
    amounts=sorted(set([1,2,10,100,1000,10000,35766,35767,10**6,10**8,500000000,999999999,10**9]+[rng.randrange(1,10**9+1) for _ in range(100)]))
    states=[(base,quote)]+[(b,q) for b in [1,100,1000000,base] for q in [1,100,20000]]
    return [{'amount_in':amount,'reserve_in':vi,'reserve_out':vq}
            for vi,vq in states
            for amount in (amounts if (vi,vq)==(base,quote) else [1,1000,10**6,10**9])]
