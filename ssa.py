from visitor import AsmGenericVisitor


class SSAVistor(AsmGenericVisitor):
    def visit_arg_list(self, node, scope):
        scope['_reg'] = []
        for arg in node[1]:
            self.visit(arg, scope)
        if scope['_reg']:
            out_reg = scope['_reg'][0]
            if out_reg[-1] not in scope['ssa_form']:
                if out_reg[1] not in scope['_ssa_reg_counter']:
                    scope['_ssa_reg_counter'][out_reg[1]] = 0
                scope['ssa_form'][out_reg[-1]] = scope['_ssa_reg_counter'][out_reg[1]] + 1

            for reg in scope['_reg'][1:]:
                if reg[1] not in scope['_ssa_reg_counter']:
                    scope['_ssa_reg_counter'][reg[1]] = 0
                scope['ssa_form'][reg[-1]] = scope['_ssa_reg_counter'][reg[1]]

            scope['_ssa_reg_counter'][out_reg[1]] += 1

    def visit_reg(self, node, scope):
        scope['_reg'] += [node]


def construct_ssa(scope):
    queue = [min(scope['cfg'].keys())]
    visited = set()

    scope['ssa_form'] = {}
    scope['_ssa_reg_counter'] = {}
    ssa_visitor = SSAVistor()

    while queue:
        curr = queue.pop(0)
        if curr not in visited:
            ssa_visitor.visit(scope['id_instruction'][curr], scope)
            nxt = scope['cfg'][curr]
            queue += nxt
            visited.add(curr)
