reg carry
reg rd
reg dr
reg [7:0] ir
reg [7:0] acc
reg [7:0] x
reg [7:0] y
reg [7:0] sr
reg [7:0] sp
reg [15:0] pc
reg [15:0] opd
reg [15:0] mdr
reg [15:0] mar
reg [7:0] mem0  [8191:0]
###################################
macro imm_read
    add pc, pc, 1
    ld mdr, mem0, pc

macro abs_read
    add pc, pc, 1
    ld mdr[7:0], mem0, pc
    add pc, pc, 1
    ld mdr[15:8], mem0, pc

macro ind_read
    add pc, pc, 1
    ld mdr[7:0], mem0, pc
    add pc, pc, 1
    ld mdr[15:0], mem0, pc

###################################
i_fetch:
    ld ir, mem0, pc
    add pc, pc, 1
i_decode:
    je ir, 69, op_adc_69_imm
    je ir, 29, op_and_29_imm
    je ir, 0A, op_asl_0A_acc
    je ir, 4C, op_jmp_4C_abs
    je ir, 6C, op_jmp_6C_ind
    jmp op_undefined
op_undefined:
#    TODO: what does 6502 do, when encountering undefined opcode?
    jmp inc_pc
op_adc_69_imm:
    imm_read
    add acc, acc, mdr
    jmp inc_pc
op_and_29_imm:
    imm_read
    and acc, acc, mdr
    jmp inc_pc
op_asl_0A_acc:
    mov carry, acc[7]
    mov acc[7:1], acc[6:0]
    mov acc[0], 0
    jmp inc_pc
op_jmp_4C_abs:
    add hi, pc, 1
    ld pc[7:0], mem0, lo
    ld pc[15:8], mem0, hi
    jmp i_fetch
op_jmp_6C_ind:
    ld lo, mem0, pc
    add mar, pc, 1
    ld hi, mem0, mar
    ld pc[15:8], mem0, lo
    ld pc[7:0], mem0, hi
    jmp i_fetch
