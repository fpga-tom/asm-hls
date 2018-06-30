from parser import parse
from gen import get_node_ast
from cfg import construct_cfg
from ssa import construct_ssa

# global dictionary for data

unit = parse("b.asm")
cfg = construct_cfg(unit)
(ssa_form, ssa_form_def, ssa_form_def_) = construct_ssa(cfg)

from hdl import find_raw, asap, clique, cover, reg_asap, reg_clique, signals, muxes, fsm, \
    generate_verilog


raw = find_raw(ssa_form, ssa_form_def_)
schedule = asap(cfg, raw)
cliques = clique(schedule, unit)
fun_cover = cover(cliques)
reg_schedule = reg_asap(schedule, ssa_form, ssa_form_def)
reg_cliques = reg_clique(reg_schedule)
reg_cover = cover(reg_cliques)
signals_in, signals_out = signals(unit, fun_cover, reg_cover, ssa_form, ssa_form_def, schedule)
muxes_in, muxes_out = muxes(signals_in, signals_out)
status_signals = fsm(muxes_in, muxes_out, signals_in, signals_out)
#

for i in get_node_ast(unit, 'instruction'):
    print(i)
print('raw', raw)
print('schedule', schedule)
print('cliques', cliques)
print('cover', fun_cover)
print('reg_asap', reg_schedule)
print('reg_clique', reg_cliques)
print('reg_cover', reg_cover)
print('signals_in', signals_in)
print('signals_out', signals_out)
print('muxes_in', muxes_in)
print('muxes_out', muxes_out)
print('fsm', status_signals)

generate_verilog(unit, fun_cover, reg_cover, signals_in, signals_out, muxes_in, muxes_out, status_signals, schedule)

# print(scope['cfg'])
# print(scope['ssa_form_def'])
# print(scope['ssa_form'])



