import networkx as nx


def find_raw(scope):
    raw = {}
    for reg, instruction in scope['ssa_form'].iteritems():
        (reg_name, ssa_id) = reg
        if ssa_id > 0:
            def_instruction = scope['ssa_form_def_'][(reg[0][1], reg[1])] # get ssa definition instruction
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


def _cover(cliques):
    cli_complement = nx.complement(nx.from_dict_of_lists(cliques))
    coloring = nx.coloring.greedy_color(cli_complement)
    result = {}
    for key, val in coloring.iteritems():
        if val not in result:
            result[val] = []
        result[val] += [key]
    return result


def cover(scope):
    cliques = scope['clique']
    result = _cover(cliques)
    scope['cover'] = result


def reg_asap(scope):
    schedule = scope['asap']
    reg_schedule = {}

    for reg, instruction in scope['ssa_form'].iteritems():
        if reg[0][1] not in reg_schedule:
            reg_schedule[reg[0][1]] = []
        reg_schedule[reg[0][1]] += schedule[instruction[-1]]

    for reg, instruction in scope['ssa_form_def'].iteritems():
        if reg[0][1] not in reg_schedule:
            reg_schedule[reg[0][1]] = []
        reg_schedule[reg[0][1]] += schedule[instruction[-1]]

    scope['reg_asap'] = reg_schedule


def reg_clique(scope):
    cli = {}
    sch = scope['reg_asap']
    for a in sch:
        a_l = []
        for b in sch:
            if not set.intersection(set(sch[a]), set(sch[b])):
                a_l = a_l + [b]
        cli[a] = a_l
    scope['reg_clique'] = cli


def reg_cover(scope):
    cliques = scope['reg_clique']
    result = _cover(cliques)
    scope['reg_cover'] = result


def signals(scope):
    sig = {}
    result = {}
    cover = scope['cover']
    cover_reverse = {vv:k for k, v in cover.iteritems() for vv in v}
    reg_cover = scope['reg_cover']
    reg_cover_reverse = {vv: k for k, v in reg_cover.iteritems() for vv in v}

    for reg_ssa, instruction in scope['ssa_form'].iteritems():
        (reg, ssa) = reg_ssa
        sig[(reg[-1], instruction[-1])] = scope['asap'][instruction[-1]]

    for id_reg_id_instruction, control_step in sig.iteritems():
        (id_reg, id_instruction) = id_reg_id_instruction
        id_funit = cover_reverse[id_instruction]
        reg_name = scope['id_reg'][id_reg][1]
        reg_slot = scope['id_reg_slot'][id_reg]
        id_runit = reg_cover_reverse[reg_name]
        if (id_runit, id_funit, reg_slot) not in result:
            result[(id_runit, id_funit, reg_slot)] =[]
        result[(id_runit, id_funit, reg_slot)] += control_step

    scope['signals_in'] = result

    sig = {}
    result = {}
    for reg_ssa, instruction in scope['ssa_form_def'].iteritems():
        (reg, ssa) = reg_ssa
        sig[(instruction[-1], reg[-1])] = scope['asap'][instruction[-1]]

    for id_instruction_id_reg, control_step in sig.iteritems():
        (id_instruction, id_reg) = id_instruction_id_reg
        id_funit = cover_reverse[id_instruction]
        reg_name = scope['id_reg'][id_reg][1]
        id_runit = reg_cover_reverse[reg_name]
        if (id_funit, id_runit) not in result:
            result[(id_funit, id_runit)] =[]
        result[(id_funit, id_runit)] += control_step

    scope['signals_out'] = result


def muxes(scope):
    keys = scope['signals_in'].keys()
    mux = {}
    for i, j in enumerate(keys):
        for k in keys[i+1:]:
            if j[1] == k[1] and j[2] == k[2]:
                mux_id = (j[1], j[2])
                if mux_id not in mux:
                    mux[mux_id] = []
                mux[mux_id] += [j, k]

    scope['muxes_in'] = mux

    keys = scope['signals_out'].keys()
    mux = {}
    for i, j in enumerate(keys):
        for k in keys[i+1:]:
            if j[1] == k[1]:
                mux_id = j[1]
                if mux_id not in mux:
                    mux[mux_id] = []
                mux[mux_id] += [j, k]

    scope['muxes_out'] = mux


def fsm(scope):
    status_signals = {}
    for mux, sig in scope['muxes_in'].iteritems():
        for i, s in enumerate(sig):
            control_steps = scope['signals_in'][s]
            for control_step in control_steps:
                if control_step not in status_signals:
                    status_signals[control_step] = {}
                if mux not in status_signals[control_step]:
                    status_signals[control_step][mux] = {}
                status_signals[control_step][mux] = i

    for mux, sig in scope['muxes_out'].iteritems():
        for i, s in enumerate(sig):
            control_steps = scope['signals_out'][s]
            for control_step in control_steps:
                if control_step not in status_signals:
                    status_signals[control_step] = {}
                if mux not in status_signals[control_step]:
                    status_signals[control_step][mux] = {}
                status_signals[control_step][mux] = i

    scope['fsm'] = status_signals

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
