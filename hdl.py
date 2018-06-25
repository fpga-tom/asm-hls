import networkx as nx

def _reg_list(i):
    return i[1]

def _read(i):
    return _reg_list(i)[1:]

def _read_set(i):
    return set(_read(i))

def _write(i):
    return [_reg_list(i)[0]]

def _write_set(i):
    return set(_write(i))

def find_raw(scope):
    raw = {}
    for reg, instruction in scope['ssa_form'].iteritems():
        (reg_name, ssa_id) = reg
        if ssa_id > 0:
            def_instruction = scope['ssa_form_def'][(reg[0][1], reg[1])] # get ssa definition instruction
            if instruction[-1] not in raw:
                raw[instruction[-1]] = []
            raw[instruction[-1]] += [def_instruction[-1]]
    scope['raw'] = raw

def asap(scope):
    control_step = {}
    queue = [min(scope['cfg'].keys())]
    visited = set()

    while queue:
        curr = queue.pop(0)
        if curr not in visited:
            if scope['id_instruction'][curr][1][1] not in ['jmp']:
                if curr not in scope['raw']:
                    control_step[curr] = [0]
                else:
                    control_step[curr] = [max(control_step[x][0] for x in scope['raw'][curr]) + 1]

            nxt = scope['cfg'][curr]
            queue += nxt
            visited.add(curr)

    scope['asap'] = control_step


def clique(scope):
    cli = {}
    sch = scope['asap']
    for a in sch:
        a_l = []
        for b in sch:
            if not set.intersection(set(sch[a]), set(sch[b])):
                if scope['id_instruction'][a][1][1] == scope['id_instruction'][b][1][1]:
                    a_l = a_l + [b]
        cli[a] = a_l
    scope['clique'] = cli


def cover(scope):
    cliques = scope['clique']
    cli_complement = nx.complement(nx.from_dict_of_lists(cliques))
    coloring = nx.coloring.greedy_color(cli_complement)
    result = {}
    for key, val in coloring.iteritems():
        if val not in result:
            result[val] = []
        result[val] += [key]
    scope['cover'] = [set(l) for k,l in result.iteritems()]


def reg_schedule(scope):
    schedule = scope['asap']
    reg_schedule = {}
    for f, t in schedule.iteritems():
        for r in _reg_list(comp_unit[f]):
            if r not in reg_schedule:
                reg_schedule[r] = []
            reg_schedule[r] += t

    return reg_schedule

#
#
# def reverse(y):
#     return {z:xi for xi, x in enumerate(y) for z in x}
#
#
#
#

#
#
# def find_signals(_reg_cover_reverse, _fun_cover, _fun_cover_reverse):
#     signals = {}
#     fun = {}
#     for i, f in _fun_cover_reverse.iteritems():
#         for ri, r in enumerate(_read(comp_unit[i])):
#             fn = 'f'+ "_" + str(f) + "_" + str(ri)
#             if fn not in signals:
#                 signals[fn] = []
#                 fun[fn] = f
#             signals[fn] += [str(_reg_cover_reverse[r])]
#
#     return signals, fun
#
# def find_signals_regs(_reg_cover_reverse, _fun_cover, _fun_cover_reverse):
#     signals = {}
#     fun = {}
#     for i, f in _fun_cover_reverse.iteritems():
#         for ri, r in enumerate(_write(comp_unit[i])):
#             fn = str(_reg_cover_reverse[r])
#             if fn not in signals:
#                 signals[fn] = set()
#                 fun[fn] = f
#             signals[fn] = set.union(signals[fn], set(['f_' + str(f)]))
#
#     return signals, fun
#
#
# def find_reg_in_mux(signals):
#     result = {}
#     for key, val in signals.iteritems():
#         for v in val:
#             if v not in result:
#                 result[v] = []
#             result[v] += [key]
#     return result
#
#
# def active(sch, _mux, _fun_cover_reverse, _reg_cover_reverse):
#     m = max([max(v) for k,v in sch.iteritems()]) + 1
#     act = {}
#     for i in range(0, m):
#         a = [k for k,v in sch.iteritems() if v[0] == i]
#         for j in a:
#             for ri, r in enumerate(_read(comp_unit[j])):
#                 act_reg = str(_reg_cover_reverse[r])
#                 act_fn = 'f_' + str(_fun_cover_reverse[j]) +  '_' + str(ri)
#                 act_in = _mux[act_fn].index(act_reg)
#                 if act_fn not in act:
#                     act[act_fn] = []
#                 act[act_fn] += [{i: act_in}]
#     return act
#
# def active_reg_in_mux(sch, _mux, _fun_cover_reverse, _reg_cover_reverse):
#     m = max([max(v) for k,v in sch.iteritems()]) + 1
#     act = {}
#     for i in range(0, m):
#         a = [k for k,v in sch.iteritems() if v[0] == i]
#         for j in a:
#             for ri, r in enumerate(_write(comp_unit[j])):
#                 act_reg = str(_reg_cover_reverse[r])
#                 act_fn = 'f_' + str(_fun_cover_reverse[j])
#                 act_in = list(_mux[act_reg]).index(act_fn)
#                 if act_reg not in act:
#                     act[act_reg] = []
#                 act[act_reg] += [{i: act_in}]
#     return act
#
#
#
# # functional units
# schedule = asap(raw)
# print'schedule'
# print(schedule)
# # construct graph
# cli = clique(schedule)
# print 'graph'
# print cli
# # find clique cover
# fun = cover(cli)
# fun_reverse = reverse(fun)
# print '_fun'
# print(fun)
# print '_fun_cover_reverse'
# print(fun_reverse)
#
#
#
# # registers
# r_schedule = reg_schedule(schedule)
# print('registers schedule')
# print(r_schedule)
# rc = clique(r_schedule)
# print('registers graph')
# print(rc)
# reg_cov = cover(rc)
# reg_cov_reverse = reverse(reg_cov)
# print('reg_cover')
# print reg_cov
# print('reg_cover_reverse')
# print reg_cov_reverse
#
#
# # input muxes to funs
# signals, fun_input = find_signals(reg_cov_reverse, fun, fun_reverse)
# print('signals')
# print(signals)
#
# act = active(schedule, signals, fun_reverse, reg_cov_reverse)
# print("mux activity")
# print(act)
#
# signals_regs, reg_input = find_signals_regs(reg_cov_reverse, fun, fun_reverse)
# print('signals reg')
# print(signals_regs)
#
# print('reg_in mux')
# reg_in_mux = find_reg_in_mux(signals_regs)
# print(reg_in_mux)
#
# act_reg_in_mux = active_reg_in_mux(schedule, signals_regs, fun_reverse, reg_cov_reverse)
# print("mux reg in activity")
# print(act_reg_in_mux)
#
# from jinja2 import Environment, FileSystemLoader
#
# def generate_add(fun):
#     result = {}
#     for fi, f in enumerate(fun):
#         result[fi] = {
#                 'in0': 'f_' + str(fi) + '_0',
#                 'in1': 'f_' + str(fi) + '_1',
#                 'out': 'f_' + str(fi)
#                 }
#     return result
#
# def generate_reg(reg):
#     result = {}
#     for ri, r in enumerate(reg):
#         result[ri] = {
#                 'out': 'r'+str(ri),
#                 'in': 'm' + str(ri)
#                 }
#     return result
#
# def generate_mux(signals, fun, reg):
#     result = {}
#     for ri, r in signals.iteritems():
#         result[ri] = {
#                 'in': ['r' + str(i) for i in r],
#                 'out': ri,
#                 'ctrl': ri + "_ctrl"
#                 }
#     return result
#
# def generate_m_mux(reg_in_mux):
#     result = {}
#     for ri, r in reg_in_mux.iteritems():
#         result[ri] = {
#                 'in': [i for i in r],
#                 'out': 'm' + str(ri),
#                 'ctrl': 'm_' + ri + "_ctrl"
#                 }
#     return result
#
# def generate_fsm(schedule, mux_act, mux_reg_in_act):
#     result = {}
#     m = max([max(v) for k,v in schedule.iteritems()]) + 1
#     for i in range(0, m):
#         result[i] = {
#                 'signals': [ {xi + "_ctrl":y[i]} for xi, x in mux_act.iteritems() for y in x if i in y.keys() ]
#                 + [ {'m_'+xi + "_ctrl":y[i]} for xi, x in mux_reg_in_act.iteritems() for y in x if i in y.keys() ],
#                 'next': ((i+1) % m)
#                 }
#     return result
#
#
#
# def generate_verilog(fun, reg, signals, signals_regs):
#     file_loader = FileSystemLoader('templates')
#     env = Environment(loader=file_loader)
#
#     template_adder = env.get_template('adder.v')
#     output_adder = template_adder.render()
#
#     template_mux = env.get_template('mux.v')
#     output_mux = template_mux.render()
#
#     template_register = env.get_template('register.v')
#     output_register = template_register.render()
#
#     template_top = env.get_template('top.v')
#     output_top = template_top.render({
#         'regs' : generate_reg(reg),
#         'fun': generate_add(fun),
#         'mux': generate_mux(signals, fun, reg),
#         'm_mux': generate_m_mux(signals_regs),
#         'fsm': generate_fsm(schedule, act, act_reg_in_mux)
#         })
#
#     print(output_adder)
#     print(output_mux)
#     print(output_register)
#     print(output_top)
#
# generate_verilog(fun, reg_cov, signals, signals_regs)
#
#
#
