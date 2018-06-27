from visitor import AsmGenericVisitor


class SSAVistor(AsmGenericVisitor):
    def is_output(self, opcode, idx):
        if opcode[1] in ['mov', 'add', 'and', 'mul']:
            return idx == 0
        return False

    def is_input(self, opcode, idx):
        if opcode[1] in ['mov', 'add', 'and', 'mul']:
            return idx > 0
        if opcode[1] in ['je', 'jne']:
            return idx == 0 or idx == 1
        return False

    def visit_arg_list(self, node, scope):
        scope['_reg'] = []
        for arg in node[1]:
            self.visit(arg, scope)
        if scope['_reg']:
            for i, reg in enumerate(scope['_reg']):
                if self.is_output(scope['_opcode'], i):
                    if scope['_opcode'][1] not in ['je', 'jne']:
                        if reg[1] not in scope['_ssa_reg_counter']:
                            scope['_ssa_reg_counter'][reg[1]] = 0
                        scope['ssa_form_def'][(reg, scope['_ssa_reg_counter'][reg[1]] + 1)] = scope['_instruction']
                        scope['ssa_form_def_'][(reg[1], scope['_ssa_reg_counter'][reg[1]] + 1)] = scope['_instruction']

                if self.is_input(scope['_opcode'], i):
                    if reg[1] not in scope['_ssa_reg_counter']:
                        scope['_ssa_reg_counter'][reg[1]] = 0
                    scope['ssa_form'][(reg, scope['_ssa_reg_counter'][reg[1]])] = scope['_instruction']

                if self.is_output(scope['_opcode'], i):
                    if scope['_opcode'][1] not in ['je', 'jne']:
                        scope['_ssa_reg_counter'][reg[1]] += 1

    def visit_reg(self, node, scope):
        scope['_reg'] += [node]

    def visit_opcode(self, node, scope):
        scope['_opcode'] = node

    def visit_instruction(self, node, scope):
        scope['_instruction'] = node
        super(SSAVistor, self).visit_instruction(node, scope)


def construct_ssa(scope):
    queue = [min(scope['cfg'].keys())]
    visited = set()

    scope['ssa_form'] = {}
    scope['ssa_form_def'] = {}
    scope['ssa_form_def_'] = {}
    scope['_ssa_reg_counter'] = {}
    ssa_visitor = SSAVistor()

    while queue:
        curr = queue.pop(0)
        if curr not in visited:
            ssa_visitor.visit(scope['id_instruction'][curr], scope)
            nxt = scope['cfg'][curr]
            queue += nxt
            visited.add(curr)
