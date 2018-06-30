from gen import get_node_ast


def construct_cfg(unit):
    '''
    Builds control flow graph from AST
    :param unit: root of AST
    :return: control flow graph
    '''
    cfg = {}
    prev_instruction = None
    for instruction in get_node_ast(unit, 'instruction'):
        opcode = next(get_node_ast(instruction, 'opcode'))
        cfg[instruction] = []

        if opcode[1] in ['jmp', 'je', 'jne', 'jl', 'jg']:
            label = next(get_node_ast(instruction, 'label'))
            label_def = min([l for l in get_node_ast(unit, 'label_def') if l[1] == label[1]], key=lambda x: x[-1])
            instruction_def = min([i for i in get_node_ast(unit, 'instruction') if i[-1] > label_def[-1]], key=lambda x: x[-1])
            cfg[instruction] += [instruction_def]

        if prev_instruction and next(get_node_ast(prev_instruction, 'opcode'))[1] != 'jmp':
            cfg[prev_instruction] += [instruction]

        prev_instruction = instruction
    return cfg