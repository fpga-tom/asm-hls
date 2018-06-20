import ply.lex as lex
import re
import ply.yacc as yacc

reserved = {
    'alias' : 'ALIAS',
    'macro' : 'MACRO_DEF',
    'inc' : 'INC',
    'mov' : 'MOV',
    'set' : 'SET',
    'clr' : 'CLR',
    'jmp' : 'JMP',
    'je' : 'JE',
    'jne' : 'JNE',
    'add' : 'ADD',
    'and' : 'AND'
}

tokens = [ 'REG', 'MACRO', 'LABEL', 'COMMENT', 'NUMBER', 'COMMA', 'ID', 'EQ', 'COLON', 'LEFT', 'RIGHT', 'NEWLINE'] \
         + list(reserved.values())

t_NUMBER = r'[0-9A-F]+'
t_COMMA = r','
t_EQ = r'='
t_COLON = r':'
t_LEFT = r'\['
t_RIGHT = r'\]'

t_ignore = ' \t'

alias = []
macro = []
label = []

def p_unit(p):
    '''unit : statement NEWLINE
            | unit statement NEWLINE'''
    if len(p) == 2:
        p[0] = ('unit', p[1])
    else:
        p[0] = ('unit', p[1], p[2])

def t_NEWLINE(t):
    r'\n'
    t.lexer.lineno += len(t.value)
    return t

def p_statement(p):
    '''statement : alias
        | macro_def
        | label_def
        | COMMENT
        | MACRO
        | instruction_list'''
    p[0] = ('statement', p[1])

def p_alias(p):
    '''alias : ALIAS ID EQ reg_range'''
    global alias
    p[0] = ('alias', p[2], p[4])
    alias += [p[2]]

def p_macro_def(p):
    '''macro_def : MACRO_DEF ID NEWLINE unit'''
    global macro
    p[0] = ('macro', p[2], p[4])
    macro += [p[2]]
    print(macro)


def p_instruction(p):
    '''instruction : opcode arg_list'''
    # p[0] = ('instruction', p[1], p[2])

def p_instruction_list(p):
    '''instruction_list : instruction
        | instruction_list instruction'''
    if len(p) == 2:
        p[0] = ('instruction_list', p[1])
    else:
        p[0] = ('instruction_list', p[1], p[2])

def p_range_1(p):
    '''range : LEFT NUMBER COLON NUMBER RIGHT'''
    p[0] = ('range', p[2], p[4])

def p_range_2(p):
    '''range : LEFT NUMBER RIGHT'''
    p[0] = ('range', p[2])

def p_reg(p):
    '''reg : REG'''
    p[0] = ('reg', p[1])

def p_reg_range(p):
    '''reg_range : reg
        | reg range'''
    if len(p) == 3:
        p[0] = ('reg_range', p[1], p[2])

def p_arg(p):
    '''arg : ID
        | LABEL
        | NUMBER
        | reg_range'''

def p_arg_list(p):
    '''arg_list : arg
        | arg_list COMMA arg'''

def p_opcode(p):
    '''opcode : INC
     | MOV
     | SET
     | CLR
     | JMP
     | JE
     | JNE
     | ADD
     | AND'''
    p[0] = ('opcode', p[1])

def p_label(p):
    '''label_def : ID COLON'''
    p[0] = ('label', p[1])
    global label
    label += [p[1]]

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    global alias
    if re.match('r[0-9]+', t.value) or t.value in alias:
        t.type = 'REG'
    elif t.value in macro:
        t.type = 'MACRO'
    elif t.value in label:
        t.type = 'LABEL'
    else:
        t.type = reserved.get(t.value,'ID')    # Check for reserved words
    return t

def t_COMMENT(t):
    r'\#.*'
    return t



def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


lex.lex()
parser = yacc.yacc()

import networkx as nx
import sys
f = open("a.asm")
comp_unit = parser.parse(f.read())
f.close()
print(comp_unit)


class NodeVisitor(object):
    def visit(self, node):
        method_name = 'visit_' + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception('No visit_{} method'.format(type(node).__name__))


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

def find_raw():
    raw = {}
    for i in range(0, len(comp_unit)):
        for j in range(i+1, len(comp_unit)):
            if set.intersection(_read_set(comp_unit[j]), _write_set(comp_unit[i])):
                    raw[j] = i
    return raw

def find_war():
    war = {}
    for i in range(0, len(comp_unit)):
        for j in range(i+1, len(comp_unit)):
            if set.intersection(_write_set(comp_unit[j]), _read_set(comp_unit[i])):
                    war[j] = i
    return war

def find_waw():
    waw = {}
    for i in range(0, len(comp_unit)):
        for j in range(i+1, len(comp_unit)):
            if set.intersection(_write_set(comp_unit[j]), _write_set(comp_unit[i])):
                    waw[j] = i
    return waw

def data_dependencies():
    return (find_raw(), find_war(), find_waw())

def eliminate(raw, war):
    for k,v in war.iteritems():
        if not k in raw or raw[k] != v:
            _reg = comp_unit[v][1][1]
            reg = _reg + "_" + str(k)
            comp_unit[k][1][0] = reg
            for j in range(k+1, len(comp_unit)):
                if comp_unit[j][1][0] == _reg:
                    comp_unit[j][1][0] = reg
                if comp_unit[j][1][1] == _reg:
                    comp_unit[j][1][1] = reg
                if comp_unit[j][1][2] == _reg:
                    comp_unit[j][1][2] = reg

def asap(raw):
    control_step = {}
    for i in range(0, len(comp_unit)):
        if not i in raw:
            control_step[i] = [0]
        else:
            control_step[i] = [max(control_step[raw[i]]) + 1]
    return control_step



def clique(sch):
    cli = {}
    for a in sch:
        a_l = []
        for b in sch:
            if not set.intersection(set(sch[a]), set(sch[b])):
                a_l = a_l + [b]
        cli[a] = a_l
    return cli


def reverse(y):
    return {z:xi for xi, x in enumerate(y) for z in x}


def cover(cliques):
    cli_complement = nx.complement(nx.from_dict_of_lists(cliques))
    coloring = nx.coloring.greedy_color(cli_complement)
    result = {}
    for key, val in coloring.iteritems():
        if val not in result:
            result[val] = []
        result[val] += [key]
    return [set(l) for k,l in result.iteritems()]


def reg_schedule(schedule):
    result = {}
    reg_schedule = {}
    for f, t in schedule.iteritems():
        for r in _reg_list(comp_unit[f]):
            if r not in reg_schedule:
                reg_schedule[r] = []
            reg_schedule[r] += t

    return reg_schedule


def find_signals(_reg_cover_reverse, _fun_cover, _fun_cover_reverse):
    signals = {}
    fun = {}
    for i, f in _fun_cover_reverse.iteritems():
        for ri, r in enumerate(_read(comp_unit[i])):
            fn = 'f'+ "_" + str(f) + "_" + str(ri)
            if fn not in signals:
                signals[fn] = []
                fun[fn] = f
            signals[fn] += [str(_reg_cover_reverse[r])]

    return signals, fun

def find_signals_regs(_reg_cover_reverse, _fun_cover, _fun_cover_reverse):
    signals = {}
    fun = {}
    for i, f in _fun_cover_reverse.iteritems():
        for ri, r in enumerate(_write(comp_unit[i])):
            fn = str(_reg_cover_reverse[r])
            if fn not in signals:
                signals[fn] = set()
                fun[fn] = f
            signals[fn] = set.union(signals[fn], set(['f_' + str(f)]))

    return signals, fun


def find_reg_in_mux(signals):
    result = {}
    for key, val in signals.iteritems():
        for v in val:
            if v not in result:
                result[v] = []
            result[v] += [key]
    return result


def active(sch, _mux, _fun_cover_reverse, _reg_cover_reverse):
    m = max([max(v) for k,v in sch.iteritems()]) + 1
    act = {}
    for i in range(0, m):
        a = [k for k,v in sch.iteritems() if v[0] == i]
        for j in a:
            for ri, r in enumerate(_read(comp_unit[j])):
                act_reg = str(_reg_cover_reverse[r])
                act_fn = 'f_' + str(_fun_cover_reverse[j]) +  '_' + str(ri)
                act_in = _mux[act_fn].index(act_reg)
                if act_fn not in act:
                    act[act_fn] = []
                act[act_fn] += [{i: act_in}]
    return act

def active_reg_in_mux(sch, _mux, _fun_cover_reverse, _reg_cover_reverse):
    m = max([max(v) for k,v in sch.iteritems()]) + 1
    act = {}
    for i in range(0, m):
        a = [k for k,v in sch.iteritems() if v[0] == i]
        for j in a:
            for ri, r in enumerate(_write(comp_unit[j])):
                act_reg = str(_reg_cover_reverse[r])
                act_fn = 'f_' + str(_fun_cover_reverse[j])
                act_in = list(_mux[act_reg]).index(act_fn)
                if act_reg not in act:
                    act[act_reg] = []
                act[act_reg] += [{i: act_in}]
    return act


raw, war, waw = data_dependencies()
print("RAW: ", raw)
print("WAR: ", war)
print("WAW: ", waw)

while True:
    raw, war, waw = data_dependencies()
    eliminate(raw, war)
#    raw, war, waw = data_dependencies()
#    eliminate(raw, waw)
    break

print(comp_unit)
raw, war, waw = data_dependencies()
print("RAW: ", raw)
print("WAR: ", war)
print("WAW: ", waw)




# functional units
schedule = asap(raw)
print'schedule'
print(schedule)
# construct graph
cli = clique(schedule)
print 'graph'
print cli
# find clique cover
fun = cover(cli)
fun_reverse = reverse(fun)
print '_fun'
print(fun)
print '_fun_cover_reverse'
print(fun_reverse)



# registers
r_schedule = reg_schedule(schedule)
print('registers schedule')
print(r_schedule)
rc = clique(r_schedule)
print('registers graph')
print(rc)
reg_cov = cover(rc)
reg_cov_reverse = reverse(reg_cov)
print('reg_cover')
print reg_cov
print('reg_cover_reverse')
print reg_cov_reverse


# input muxes to funs
signals, fun_input = find_signals(reg_cov_reverse, fun, fun_reverse)
print('signals')
print(signals)

act = active(schedule, signals, fun_reverse, reg_cov_reverse)
print("mux activity")
print(act)

signals_regs, reg_input = find_signals_regs(reg_cov_reverse, fun, fun_reverse)
print('signals reg')
print(signals_regs)

print('reg_in mux')
reg_in_mux = find_reg_in_mux(signals_regs)
print(reg_in_mux)

act_reg_in_mux = active_reg_in_mux(schedule, signals_regs, fun_reverse, reg_cov_reverse)
print("mux reg in activity")
print(act_reg_in_mux)

from jinja2 import Environment, FileSystemLoader

def generate_add(fun):
    result = {}
    for fi, f in enumerate(fun):
        result[fi] = {
                'in0': 'f_' + str(fi) + '_0',
                'in1': 'f_' + str(fi) + '_1',
                'out': 'f_' + str(fi)
                }
    return result

def generate_reg(reg):
    result = {}
    for ri, r in enumerate(reg):
        result[ri] = {
                'out': 'r'+str(ri),
                'in': 'm' + str(ri)
                }
    return result

def generate_mux(signals, fun, reg):
    result = {}
    for ri, r in signals.iteritems():
        result[ri] = {
                'in': ['r' + str(i) for i in r],
                'out': ri,
                'ctrl': ri + "_ctrl"
                }
    return result

def generate_m_mux(reg_in_mux):
    result = {}
    for ri, r in reg_in_mux.iteritems():
        result[ri] = {
                'in': [i for i in r],
                'out': 'm' + str(ri),
                'ctrl': 'm_' + ri + "_ctrl"
                }
    return result

def generate_fsm(schedule, mux_act, mux_reg_in_act):
    result = {}
    m = max([max(v) for k,v in schedule.iteritems()]) + 1
    for i in range(0, m):
        result[i] = {
                'signals': [ {xi + "_ctrl":y[i]} for xi, x in mux_act.iteritems() for y in x if i in y.keys() ]
                + [ {'m_'+xi + "_ctrl":y[i]} for xi, x in mux_reg_in_act.iteritems() for y in x if i in y.keys() ],
                'next': ((i+1) % m)
                }
    return result



def generate_verilog(fun, reg, signals, signals_regs):
    file_loader = FileSystemLoader('templates')
    env = Environment(loader=file_loader)

    template_adder = env.get_template('adder.v')
    output_adder = template_adder.render()

    template_mux = env.get_template('mux.v')
    output_mux = template_mux.render()

    template_register = env.get_template('register.v')
    output_register = template_register.render()

    template_top = env.get_template('top.v')
    output_top = template_top.render({
        'regs' : generate_reg(reg),
        'fun': generate_add(fun),
        'mux': generate_mux(signals, fun, reg),
        'm_mux': generate_m_mux(signals_regs),
        'fsm': generate_fsm(schedule, act, act_reg_in_mux)
        })

    print(output_adder)
    print(output_mux)
    print(output_register)
    print(output_top)

generate_verilog(fun, reg_cov, signals, signals_regs)



