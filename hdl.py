import networkx as nx
from gen import get_node_ast, get_node_cfg
from ssa import invert_dict


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


def clique(sch, unit):
    cli = {}
    for a in sch:
        a_l = []
        instruction_a, *_ = [x for x in get_node_ast(unit, 'instruction') if x[-1] == a]
        opcode_a = next(get_node_ast(instruction_a, 'opcode'))
        for b in sch:
            instruction_b, *_ = [x for x in get_node_ast(unit, 'instruction') if x[-1] == b]
            opcode_b = next(get_node_ast(instruction_b, 'opcode'))
            if not set.intersection(set(sch[a]), set(sch[b])):
                if opcode_a[1] == opcode_b[1]:
                    a_l = a_l + [b]
        cli[a] = a_l
    return cli


def cover(cliques):
    cli_complement = nx.complement(nx.from_dict_of_lists(cliques))
    coloring = nx.coloring.greedy_color(cli_complement)
    result = {}
    for key, val in coloring.items():
        if val not in result:
            result[val] = []
        result[val] += [key]
    return result


def reg_asap(schedule, ssa_form, ssa_form_def):
    reg_schedule = {}

    for reg, instruction in ssa_form.items():
        if reg[0][1] not in reg_schedule:
            reg_schedule[reg[0][1]] = []
        reg_schedule[reg[0][1]] += schedule[instruction[-1]]

    for reg, instruction in ssa_form_def.items():
        if reg[0][1] not in reg_schedule:
            reg_schedule[reg[0][1]] = []
        reg_schedule[reg[0][1]] += schedule[instruction[-1]]

    return reg_schedule


def reg_clique(sch):
    cli = {}
    for a in sch:
        a_l = []
        for b in sch:
            if not set.intersection(set(sch[a]), set(sch[b])):
                a_l = a_l + [b]
        cli[a] = a_l
    return cli


def signals(unit, fun_cover, reg_cover, ssa_form, ssa_form_def, schedule):
    '''
    Creates dict of signals and assign control step to each one
    :param unit:
    :param cover:
    :param reg_cover:
    :param ssa_form:
    :param ssa_form_def:
    :param schedule:
    :return:
    '''
    sig = {}
    result = {}
    cover_reverse = invert_dict(fun_cover)
    reg_cover_reverse = invert_dict(reg_cover)

    for reg_ssa, instruction in ssa_form.items():
        (reg, ssa) = reg_ssa
        sig[(reg[-1], instruction[-1])] = schedule[instruction[-1]]

    for id_reg_id_instruction, control_step in sig.items():
        (id_reg, id_instruction) = id_reg_id_instruction
        id_funit, *_ = cover_reverse[id_instruction]
        reg_name, *_ = [arg[1][1] for arg in get_node_ast(unit, 'arg')
                        if id_reg in
                        [next(get_node_ast(arg, 'reg'), [-1])[-1],
                         next(get_node_ast(arg, 'number'), [-1])[-1]]]
        instruction, *_ = [x for x in get_node_ast(unit, 'instruction') if x[-1] == id_instruction]
        args = get_node_ast(instruction, 'arg')
        reg_slot, *_ = [i for i, arg in enumerate(args)
                        if id_reg == next(get_node_ast(arg, 'reg'), [-1])[-1] or
                        id_reg == next(get_node_ast(arg, 'number'), [-1])[-1]]
        id_runit, *_ = reg_cover_reverse[reg_name]
        if (id_runit, id_funit, reg_slot) not in result:
            result[(id_runit, id_funit, reg_slot)] = []
        result[(id_runit, id_funit, reg_slot)] += control_step

    signals_in = result

    sig = {}
    result = {}
    for reg_ssa, instruction in ssa_form_def.items():
        (reg, ssa) = reg_ssa
        sig[(instruction[-1], reg[-1])] = schedule[instruction[-1]]

    for id_instruction_id_reg, control_step in sig.items():
        (id_instruction, id_reg) = id_instruction_id_reg
        id_funit, *_ = cover_reverse[id_instruction]
        reg_name, *_ = [x[1] for x in get_node_ast(unit, 'reg') if x[-1] == id_reg]
        id_runit, *_ = reg_cover_reverse[reg_name]
        if (id_funit, id_runit) not in result:
            result[(id_funit, id_runit)] =[]
        result[(id_funit, id_runit)] += control_step

    signals_out = result

    return signals_in, signals_out


def muxes(signals_in, signals_out):
    keys = list(signals_in.keys())
    mux = {}
    for i, j in enumerate(keys):
        for k in keys[i+1:]:
            if j[1] == k[1] and j[2] == k[2]:
                mux_id = (j[1], j[2])
                if mux_id not in mux:
                    mux[mux_id] = []
                mux[mux_id] += [j, k]

    muxes_in = mux

    keys = list(signals_out.keys())
    mux = {}
    for i, j in enumerate(keys):
        for k in keys[i+1:]:
            if j[1] == k[1]:
                mux_id = j[1]
                if mux_id not in mux:
                    mux[mux_id] = []
                mux[mux_id] += [j, k]

    muxes_out = mux
    return muxes_in, muxes_out


def fsm(muxes_in, muxes_out, signals_in, signals_out):
    status_signals = {}
    for mux, sig in muxes_in.items():
        for i, s in enumerate(sig):
            control_steps = signals_in[s]
            for control_step in control_steps:
                if control_step not in status_signals:
                    status_signals[control_step] = {}
                if mux not in status_signals[control_step]:
                    status_signals[control_step][mux] = {}
                status_signals[control_step][mux] = i

    for mux, sig in muxes_out.items():
        for i, s in enumerate(sig):
            control_steps = signals_out[s]
            for control_step in control_steps:
                if control_step not in status_signals:
                    status_signals[control_step] = {}
                if mux not in status_signals[control_step]:
                    status_signals[control_step][mux] = {}
                status_signals[control_step][mux] = i

    return status_signals


from jinja2 import Environment, FileSystemLoader


def is_fun(unit, cover, id_fun, _opcode):
    id_instruction = cover[id_fun][0]
    instruction, *_ = [x for x in get_node_ast(unit, 'instruction') if x[-1] == id_instruction]
    opcode = next(get_node_ast(instruction, 'opcode'))
    return opcode[1] == _opcode


def is_mux(mux, k):
    for m, v in mux.items():
        if k in v:
            return True
    return False


def generate_opcode(unit, fun_cover, signals_in, signals_out, muxes_in, opcode):
    result = {}
    fun = [k for k in signals_out.keys() if is_fun(unit, fun_cover, k[0], opcode)]
    for f in fun:
        if 'fun_' + str(f[0]) not in result:
            result['fun_' + str(f[0])] = {}
        result['fun_' + str(f[0])]['out'] = 'fun_out_' + str(f[0])

    fun = [k for k in signals_in.keys() if is_fun(unit, fun_cover, k[1], opcode)]
    for f in fun:
        fi = "_".join(map(str, f))
        if 'fun_' + str(f[1]) not in result:
            result['fun_' + str(f[1])] = {}
        if not is_mux(muxes_in, f):
            result['fun_' + str(f[1])]['in' + str(f[2])] = 'reg_out_' + str(f[0])
        else:
            result['fun_' + str(f[1])]['in' + str(f[2])] = 'mux_out_' + str(f[1]) + '_' + str(f[2])
    return result


def generate_mux(mux_in, mux_out):
    result = {}
    for mux, r in mux_out.items():
        fi = str(mux)
        for i, fun in enumerate(r):
            if 'mux_' + fi not in result:
                result['mux_' + fi] = {}
            result['mux_' + fi]['in' + str(i)] = 'fun_out_' + str(fun[0])
        result['mux_' + fi]['out'] = 'mux_out_' + fi

    for mux, r in mux_in.items():
        fi = '_'.join(map(str, mux))
        for i, reg in enumerate(r):
            if 'mux_' + fi not in result:
                result['mux_' + fi] = {}
            result['mux_' + fi]['in' + str(i)] = 'reg_out_' + str(reg[0])
        result['mux_' + fi]['out'] = 'mux_out_' + fi
    return result


def generate_reg(reg_cover, signals_out, muxes_out):
    result = {}
    for r, v in reg_cover.items():
        result['reg_' + str(r)] = {'out': 'reg_out_' + str(r)}

    for k, v in signals_out.items():
        if not is_mux(muxes_out, k):
            result['reg_' + str(k[1])]['in'] = 'fun_out_' + str(k[0])
        else:
            result['reg_' + str(k[1])]['in'] = 'mux_out_' + str(k[1])
    return result

def generate_fsm(fsm, schedule):
    result = {}
    for control_step, signals in fsm.items():
        sigs = {'mux_' + '_'.join(map(str, k if isinstance(k, tuple) else [k])): v for k, v in signals.items()}
        result[control_step] = {
            'state': control_step,
            'next_state': (control_step + 1) % (max(x[0] for x in schedule.values()) + 1),
            'signals': sigs
        }
    return result


def generate_verilog(unit, fun_cover, reg_cover, signals_in, signals_out, muxes_in, muxes_out, status_signals, schedule):
    file_loader = FileSystemLoader('templates')
    env = Environment(loader=file_loader)

    template_top = env.get_template('top.v')
    all_signals = set()
    _reg = generate_reg(reg_cover, signals_out, muxes_out)
    _add = generate_opcode(unit, fun_cover, signals_in, signals_out, muxes_in, 'add')
    _mul = generate_opcode(unit, fun_cover, signals_in, signals_out, muxes_in, 'mul')
    _mov = generate_opcode(unit, fun_cover, signals_in, signals_out, muxes_in, 'mov')
    _jl = generate_opcode(unit, fun_cover, signals_in, signals_out, muxes_in, 'jl')
    _mux =generate_mux(muxes_in, muxes_out)
    all_signals |= set([ v['out'] for k, v in _reg.items()])
    all_signals |= set([ v['out'] for k, v in _add.items()])
    all_signals |= set([ v['out'] for k, v in _mul.items()])
    all_signals |= set([ v['out'] for k, v in _mov.items()])
    all_signals |= set([ v['out'] for k, v in _mux.items()])
    all_signals |= set([ k  for k, v in _mux.items()])
    output_top = template_top.render({
        'regs' : generate_reg(reg_cover, signals_out, muxes_out),
        'add': generate_opcode(unit, fun_cover, signals_in, signals_out, muxes_in, 'add'),
        'mul': generate_opcode(unit, fun_cover, signals_in, signals_out, muxes_in, 'mul'),
        'mov': generate_opcode(unit, fun_cover, signals_in, signals_out, muxes_in, 'mov'),
        'mux': generate_mux(muxes_in, muxes_out),
        'fsm': generate_fsm(status_signals, schedule),
        'all_signals' : all_signals,
        'bit_width': 16,
        'bit_range': '[15:0]'
        })

    print(output_top)




