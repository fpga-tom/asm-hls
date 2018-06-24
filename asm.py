
from parser import parse
from visitor import construct_cfg
from ssa import construct_ssa

## global dictionary for data
scope = {}

scope['unit'] = parse("a.asm")
construct_cfg(scope)
construct_ssa(scope)

print(scope)

