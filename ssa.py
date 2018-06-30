from gen import get_node_cfg, get_node_ast


def is_output(instruction, arg):
    opcode = next(get_node_ast(instruction, 'opcode'))
    arg_list = next(get_node_ast(instruction, 'arg_list'))
    for idx, a in enumerate(get_node_ast(arg_list, 'arg')):
        if arg == a:
            if opcode[1] in ['mov', 'add', 'and', 'mul']:
                return idx == 0
            if opcode[1] in ['je', 'jne', 'jl', 'jg']:
                return idx == 2
    return False


def is_input(instruction, arg):
    opcode = next(get_node_ast(instruction, 'opcode'))
    arg_list = next(get_node_ast(instruction, 'arg_list'))
    for idx, a in enumerate(get_node_ast(arg_list, 'arg')):
        if arg == a:
            if opcode[1] in ['mov', 'add', 'and', 'mul']:
                return idx > 0
            if opcode[1] in ['je', 'jne', 'jl', 'jg']:
                return idx == 0 or idx == 1
    return False


def construct_ssa(cfg):
    '''
    Builds ssa form from CFG
    :param cfg: control flow graph
    :return: ssa form
    '''
    ssa_form = {}
    ssa_form_def = {}
    ssa_form_def_ = {}
    _ssa_reg_counter = {}

    for instruction in get_node_cfg(cfg):
        for arg in get_node_ast(instruction, 'arg'):
            opcode = next(get_node_ast(instruction, 'opcode'))
            if is_output(instruction, arg):
                if opcode[1] not in ['je', 'jne', 'jl', 'jg']:
                    reg = next(get_node_ast(arg, 'reg'), [])
                    if reg:
                        if reg[1] not in _ssa_reg_counter:
                            _ssa_reg_counter[reg[1]] = 0
                        ssa_form_def[(reg, _ssa_reg_counter[reg[1]] + 1)] = instruction
                        ssa_form_def_[(reg[1], _ssa_reg_counter[reg[1]] + 1)] = instruction

            if is_input(instruction, arg):
                reg = next(get_node_ast(arg, 'reg'), [])
                const = next(get_node_ast(arg, 'number'), [])
                if reg:
                    if reg[1] not in _ssa_reg_counter:
                        _ssa_reg_counter[reg[1]] = 0
                    ssa_form[(reg, _ssa_reg_counter[reg[1]])] = instruction
                if const:
                    if const[1] not in _ssa_reg_counter:
                        _ssa_reg_counter[const[1]] = 0
                    ssa_form[(const, _ssa_reg_counter[const[1]])] = instruction

            if is_output(instruction, arg):
                reg = next(get_node_ast(arg, 'reg'), [])
                if opcode[1] not in ['je', 'jne', 'jl', 'jg']:
                    _ssa_reg_counter[reg[1]] += 1

    return ssa_form, ssa_form_def, ssa_form_def_