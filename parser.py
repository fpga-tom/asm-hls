import ply.lex as lex
import re
import ply.yacc as yacc


####################################################################
####################################################################
##
## PARSER
##
## parses assembly file and returns abstract syntax tree
##
####################################################################
####################################################################

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

alias = set()
macro = set()
label = set()

node_count = 0

def p_unit(p):
    '''unit : statement NEWLINE
            | unit statement NEWLINE'''
    global node_count
    if len(p) == 3:
        p[0] = ('unit', [p[1]], node_count)
    else:
        p[0] = ('unit', p[1][1] + [p[2]], node_count)
    node_count += 1

def t_NEWLINE(t):
    r'\n'
    t.lexer.lineno += len(t.value)
    return t

def p_statement(p):
    '''statement : alias
        | macro_def
        | label_def
        | comment
        | macro
        | instruction_list'''
    global node_count
    p[0] = ('statement', p[1], node_count)
    node_count += 1

def p_macro(p):
    '''macro : MACRO'''
    global node_count
    p[0] = ('macro', p[1], node_count)
    node_count += 1

def p_comment(p):
    '''comment : COMMENT'''
    global node_count
    p[0] = ('comment', p[1], node_count)
    node_count += 1

def p_alias(p):
    '''alias : ALIAS ID EQ reg_range'''
    global alias
    global node_count
    p[0] = ('alias', p[2], p[4], node_count)
    alias.add(p[2])
    node_count += 1

def p_macro_def(p):
    '''macro_def : MACRO_DEF ID NEWLINE unit'''
    global macro
    global node_count
    p[0] = ('macro', p[2], p[4], node_count)
    macro.add(p[2])
    node_count += 1


def p_instruction(p):
    '''instruction : opcode arg_list'''
    global node_count
    p[0] = ('instruction', p[1], p[2], node_count)
    node_count += 1

def p_instruction_list(p):
    '''instruction_list : instruction
        | instruction_list instruction'''
    global node_count
    if len(p) == 2:
        p[0] = ('instruction_list', [p[1]], node_count)
    else:
        p[0] = ('instruction_list', p[1][1] + [p[2]], node_count)
    node_count += 1

def p_range_1(p):
    '''range : LEFT NUMBER COLON NUMBER RIGHT'''
    global node_count
    p[0] = ('range', p[2], p[4], node_count)
    node_count += 1

def p_range_2(p):
    '''range : LEFT NUMBER RIGHT'''
    global node_count
    p[0] = ('range', p[2], p[2], node_count)
    node_count += 1

def p_reg(p):
    '''reg : REG'''
    global node_count
    p[0] = ('reg', p[1], node_count)
    node_count += 1

def p_reg_range(p):
    '''reg_range : reg range'''
    global node_count
    p[0] = ('reg_range', p[1], p[2], node_count)
    node_count += 1

def p_label(p):
    '''label : LABEL'''
    global node_count
    p[0] = ('label', p[1], node_count)
    node_count += 1

def p_number(p):
    '''number : NUMBER'''
    global node_count
    p[0] = ('number', p[1], node_count)
    node_count += 1

def p_arg(p):
    '''arg : label
        | number
        | reg_range
        | reg'''
    global node_count
    p[0] = ('arg', p[1], node_count)
    node_count += 1

def p_arg_list(p):
    '''arg_list : arg
        | arg_list COMMA arg'''
    global node_count
    if len(p) == 2:
        p[0] = ('arg_list', [p[1]], node_count)
    else:
        p[0] = ('arg_list', p[1][1] + [p[3]], node_count)
    node_count += 1

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
    global node_count
    p[0] = ('opcode', p[1], node_count)
    node_count += 1

def p_label_def(p):
    '''label_def : LABEL COLON'''
    global node_count
    p[0] = ('label_def', p[1], node_count)
    node_count += 1

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


def parse(file):
    f = open(file)
    for line in f:
        if re.match(r'[a-zA-Z_][a-zA-Z_0-9]*:', line):
            label.add(line[:-2])
    f.close()

    lexer = lex.lex()
    parser = yacc.yacc()

    f = open(file)
    comp_unit = parser.parse(f.read())
    f.close()
    return comp_unit