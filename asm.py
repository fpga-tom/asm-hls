from parser import parse
from visitor import construct_cfg
from ssa import construct_ssa

# global dictionary for data
scope = {}

parse("b.asm", scope)
construct_cfg(scope)
construct_ssa(scope)

from hdl import find_raw

print(find_raw(scope))

print(scope['cfg'])
print(scope['ssa_form_def'])
print(scope['ssa_form'])

