from parser import parse
from visitor import construct_cfg
from ssa import construct_ssa

# global dictionary for data
scope = {}

parse("b.asm", scope)
construct_cfg(scope)
construct_ssa(scope)

from hdl import find_raw, asap, clique, cover, reg_asap, reg_clique, reg_cover, signals, muxes, fsm, \
    generate_verilog
find_raw(scope)
asap(scope)
clique(scope)
cover(scope)
reg_asap(scope)
reg_clique(scope)
reg_cover(scope)
signals(scope)
muxes(scope)
fsm(scope)

print('raw', scope['raw'])
print('asap', scope['asap'])
print('clique', scope['clique'])
print('cover', scope['cover'])
print('reg_asap', scope['reg_asap'])
print('reg_clique', scope['reg_clique'])
print('reg_cover', scope['reg_cover'])
print('signals_in', scope['signals_in'])
print('signals_out', scope['signals_out'])
print('muxes_in', scope['muxes_in'])
print('muxes_out', scope['muxes_out'])
print('fsm', scope['fsm'])

generate_verilog(scope)

# print(scope['cfg'])
# print(scope['ssa_form_def'])
# print(scope['ssa_form'])


