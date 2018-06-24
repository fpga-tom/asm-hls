####################################################################
####################################################################
##
## VISITOR
##
####################################################################
####################################################################


class NodeVisitor(object):
    def visit(self, node, scope):
        method_name = 'visit_' + node[0]
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, scope)

    def generic_visit(self, node, scope):
        raise Exception('No visit_{} method'.format(node[0]))

class AsmGenericVisitor(NodeVisitor):
    def visit_unit(self, node, scope):
        for statement in node[1]:
            self.visit(statement, scope)

    def visit_statement(self, node, scope):
        self.visit(node[1], scope)

    def visit_alias(self, node, scope):
        self.visit(node[2], scope)

    def visit_reg_range(self, node, scope):
        self.visit(node[1], scope)
        self.visit(node[2], scope)

    def visit_reg(self, node, scope):
        pass

    def visit_range(self, node, scope):
        pass

    def visit_comment(self, node, scope):
        pass

    def visit_macro(self, node, scope):
        pass

    def visit_label(self, node, scope):
        pass

    def visit_label_def(self, node, scope):
        pass

    def visit_instruction_list(self, node, scope):
        for instruction in node[1]:
            self.visit(instruction, scope)

    def visit_instruction(self, node, scope):
        self.visit(node[1], scope)
        self.visit(node[2], scope)

    def visit_opcode(self, node, scope):
        pass

    def visit_arg_list(self, node, scope):
        for arg in node[1]:
            self.visit(arg, scope)

    def visit_arg(self, node, scope):
        self.visit(node[1], scope)

    def visit_number(self, node, scope):
        pass


class AssignLabelVisitor(AsmGenericVisitor):
    label_def_id = -1

    def visit_label_def(self, node, scope):
        self.label_def_id = node[-1]
        scope['label_def'][node[1]] = self.label_def_id

    def visit_instruction(self, node, scope):
        if self.label_def_id != -1:
            scope['label_instruction'][self.label_def_id] = node[-1]
            self.label_def_id = -1
        scope['id_instruction'][node[-1]] = node


class LabelVisitor(AsmGenericVisitor):
    def visit_label(self, node, scope):
        scope['label_label_def'][node[-1]] = scope['label_def'][node[1]]


class CFGVisitor(AsmGenericVisitor):
    def visit_instruction(self, node, scope):
        self.visit(node[1], scope)
        opcode = scope['_opcode']
        scope['cfg'][node[-1]] = []
        if 'jmp' == opcode[1] or 'je' == opcode[1] or 'jne' == opcode[1]:
            self.visit(node[2], scope)
            label = scope['_label']
            label_def = scope['label_label_def'][label[-1]]
            scope['cfg'][node[-1]] = [scope['label_instruction'][label_def]]

        if '_prev_instruction' in scope:
            if scope['_prev_opcode'][1] != 'jmp':
                scope['cfg'][scope['_prev_instruction'][-1]] += [node[-1]]

        scope['_prev_instruction'] = node
        scope['_prev_opcode'] = opcode

    def visit_opcode(self, node, scope):
        scope['_opcode'] = node

    def visit_label(self, node, scope):
        scope['_label'] = node


def construct_cfg(scope):
    # assign label to each instruction
    # assign id to each label
    # establish mapping between label id and instruction id
    # map instruction id to instruction
    scope['label_instruction'] = {}
    scope['label_def'] = {}
    scope['id_instruction'] = {}

    id_visitor = AssignLabelVisitor()
    id_visitor.visit(scope['unit'], scope)

    # establish mapping between label and label definition
    scope['label_label_def'] = {}
    label_visitor = LabelVisitor()
    label_visitor.visit(scope['unit'], scope)

    # construct cfg
    scope['cfg'] = {}
    cfg_visitor = CFGVisitor()
    cfg_visitor.visit(scope['unit'], scope)
