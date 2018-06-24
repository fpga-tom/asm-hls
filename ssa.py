from visitor import AsmGenericVisitor


class SSAVistor(AsmGenericVisitor):
    def visit_arg_list(self, node, scope):
        scope['_reg'] = []
        for arg in node[1]:
            self.visit(arg)
        for reg in scope['_reg']:
            pass

    def visit_reg(self, node, scope):
        scope['_reg'] += node


def construct_ssa(scope):
    queue = [min(scope['cfg'].keys())]

    while queue:
        curr = queue.pop(0)
        nxt = [x for x in scope['cfg'][curr] if x > curr]
        queue += nxt
