import networkx as nx
from gen import get_node_ast, get_node_cfg


def find_raw(ssa_form, ssa_form_def_):
    raw = {}
    for (reg_name, ssa_id), instruction in ssa_form.items():
        if ssa_id > 0:
            def_instruction = ssa_form_def_[(reg_name[1], ssa_id)] # get ssa definition instruction
            if instruction not in raw:
                raw[instruction[-1]] = []
            raw[instruction[-1]] += [def_instruction[-1]]
    return raw


def asap(cfg, raw):
    control_step = {}

    for instruction in get_node_cfg(cfg):
        opcode = next(get_node_ast(instruction, 'opcode'))
        if opcode[1] not in ['jmp']:
            if instruction[-1] not in raw:
                control_step[instruction[-1]] = [0]
            else:
                cs = [max(control_step[x][0] for x in raw[instruction[-1]]) + 1]
                if instruction[-1] not in control_step:
                    control_step[instruction[-1]] = cs
                else:
                    control_step[instruction[-1]] += cs

    return control_step


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
    for key, val in coloring.items():
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

    for reg, instruction in scope['ssa_form'].items():
        if reg[0][1] not in reg_schedule:
            reg_schedule[reg[0][1]] = []
        reg_schedule[reg[0][1]] += schedule[instruction[-1]]

    for reg, instruction in scope['ssa_form_def'].items():
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
    '''
    Creates dict of signals and assign control step to each one
    :param scope:
    :return:
    '''
    sig = {}
    result = {}
    cover = scope['cover']
    cover_reverse = {vv:k for k, v in cover.items() for vv in v}
    reg_cover = scope['reg_cover']
    reg_cover_reverse = {vv: k for k, v in reg_cover.items() for vv in v}

    for reg_ssa, instruction in scope['ssa_form'].items():
        (reg, ssa) = reg_ssa
        sig[(reg[-1], instruction[-1])] = scope['asap'][instruction[-1]]

    for id_reg_id_instruction, control_step in sig.items():
        (id_reg, id_instruction) = id_reg_id_instruction
        id_funit = cover_reverse[id_instruction]
        reg_name = scope['id_reg'][id_reg][1]
        reg_slot = scope['id_reg_slot'][id_reg]
        id_runit = reg_cover_reverse[reg_name]
        if (id_runit, id_funit, reg_slot) not in result:
            result[(id_runit, id_funit, reg_slot)] = []
        result[(id_runit, id_funit, reg_slot)] += control_step

    scope['signals_in'] = result

    sig = {}
    result = {}
    for reg_ssa, instruction in scope['ssa_form_def'].items():
        (reg, ssa) = reg_ssa
        sig[(instruction[-1], reg[-1])] = scope['asap'][instruction[-1]]

    for id_instruction_id_reg, control_step in sig.items():
        (id_instruction, id_reg) = id_instruction_id_reg
        id_funit = cover_reverse[id_instruction]
        reg_name = scope['id_reg'][id_reg][1]
        id_runit = reg_cover_reverse[reg_name]
        if (id_funit, id_runit) not in result:
            result[(id_funit, id_runit)] =[]
        result[(id_funit, id_runit)] += control_step

    scope['signals_out'] = result


def muxes(scope):
    keys = list(scope['signals_in'].keys())
    mux = {}
    for i, j in enumerate(keys):
        for k in keys[i+1:]:
            if j[1] == k[1] and j[2] == k[2]:
                mux_id = (j[1], j[2])
                if mux_id not in mux:
                    mux[mux_id] = []
                mux[mux_id] += [j, k]

    scope['muxes_in'] = mux

    keys = list(scope['signals_out'].keys())
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
    for mux, sig in scope['muxes_in'].items():
        for i, s in enumerate(sig):
            control_steps = scope['signals_in'][s]
            for control_step in control_steps:
                if control_step not in status_signals:
                    status_signals[control_step] = {}
                if mux not in status_signals[control_step]:
                    status_signals[control_step][mux] = {}
                status_signals[control_step][mux] = i

    for mux, sig in scope['muxes_out'].items():
        for i, s in enumerate(sig):
            control_steps = scope['signals_out'][s]
            for control_step in control_steps:
                if control_step not in status_signals:
                    status_signals[control_step] = {}
                if mux not in status_signals[control_step]:
                    status_signals[control_step][mux] = {}
                status_signals[control_step][mux] = i

    scope['fsm'] = status_signals


from jinja2 import Environment, FileSystemLoader


def is_fun(scope, id_fun, opcode):
    id_cover = scope['cover'][id_fun][0]
    instruction = scope['id_instruction'][id_cover]
    return instruction[1][1] == opcode

def is_mux(mux, k):
    for m, v in mux.items():
        if k in v:
            return True
    return False

def generate_opcode(scope, opcode):
    result = {}
    signals_out = scope['signals_out']
    fun = [k for k in signals_out.keys() if is_fun(scope, k[0], opcode)]
    for f in fun:
        if 'fun_' + str(f[0]) not in result:
            result['fun_' + str(f[0])] = {}
        result['fun_' + str(f[0])]['out'] = 'fun_out_' + str(f[0])

    signals_in = scope['signals_in']
    fun = [k for k in signals_in.keys() if is_fun(scope, k[1], opcode)]
    for f in fun:
        fi = "_".join(map(str, f))
        if 'fun_' + str(f[1]) not in result:
            result['fun_' + str(f[1])] = {}
        if not is_mux(scope['muxes_in'], f):
            result['fun_' + str(f[1])]['in' + str(f[2])] = 'reg_out_' + str(f[0])
        else:
            result['fun_' + str(f[1])]['in' + str(f[2])] = 'mux_out_' + str(f[1]) + '_' + str(f[2])
    return result


def generate_mux(scope):
    result = {}
    mux_out = scope['muxes_out']
    for mux, r in mux_out.items():
        fi = str(mux)
        for i, fun in enumerate(r):
            if 'mux_' + fi not in result:
                result['mux_' + fi] = {}
            result['mux_' + fi]['in' + str(i)] = 'fun_out_' + str(fun[0])
        result['mux_' + fi]['out'] = 'mux_out_' + fi

    mux_in = scope['muxes_in']
    for mux, r in mux_in.items():
        fi = '_'.join(map(str, mux))
        for i, reg in enumerate(r):
            if 'mux_' + fi not in result:
                result['mux_' + fi] = {}
            result['mux_' + fi]['in' + str(i)] = 'reg_out_' + str(reg[0])
        result['mux_' + fi]['out'] = 'mux_out_' + fi
    return result


def generate_reg(scope):
    result = {}
    for r, v in scope['reg_cover'].items():
        result['reg_' + str(r)] = {'out': 'reg_out_' + str(r)}

    for k, v in scope['signals_out'].items():
        if not is_mux(scope['muxes_out'], k):
            result['reg_' + str(k[1])]['in'] = 'fun_out_' + str(k[0])
        else:
            result['reg_' + str(k[1])]['in'] = 'mux_out_' + str(k[1])
    return result

def generate_fsm(scope):
    result = {}
    for control_step, signals in scope['fsm'].items():
        sigs = {'mux_' + '_'.join(map(str, k if isinstance(k, tuple) else [k])): v for k, v in signals.items()}
        result[control_step] = {
            'state': control_step,
            'next_state': (control_step + 1) % (max(x[0] for x in scope['asap'].values()) + 1),
            'signals': sigs
        }
    return result


def generate_verilog(scope):
    file_loader = FileSystemLoader('templates')
    env = Environment(loader=file_loader)

    template_adder = env.get_template('adder.v')
    output_adder = template_adder.render()

    template_mux = env.get_template('mux.v')
    output_mux = template_mux.render()

    template_register = env.get_template('register.v')
    output_register = template_register.render()

    template_top = env.get_template('top.v')
    scope['all_signals'] = set()
    _reg = generate_reg(scope)
    _add = generate_opcode(scope, 'add')
    _mul = generate_opcode(scope, 'mul')
    _mov = generate_opcode(scope, 'mov')
    _jl = generate_opcode(scope, 'jl')
    _mux =generate_mux(scope)
    scope['all_signals'] |= set([ v['out'] for k, v in _reg.items()])
    scope['all_signals'] |= set([ v['out'] for k, v in _add.items()])
    scope['all_signals'] |= set([ v['out'] for k, v in _mul.items()])
    scope['all_signals'] |= set([ v['out'] for k, v in _mov.items()])
    scope['all_signals'] |= set([ v['out'] for k, v in _mux.items()])
    scope['all_signals'] |= set([ k  for k, v in _mux.items()])
    output_top = template_top.render({
        'regs' : generate_reg(scope),
        'add': generate_opcode(scope, 'add'),
        'mul': generate_opcode(scope, 'mul'),
        'mov': generate_opcode(scope, 'mov'),
        'mux': generate_mux(scope),
        'fsm': generate_fsm(scope),
        'all_signals' : scope['all_signals'],
        'bit_width': 16,
        'bit_range': '[15:0]'
        })

    print(output_top)




