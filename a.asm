alias mar = r0[15:0]
alias pc = r1[15:0]
alias rd = r2[0:0]
alias dr = r3[0:0]
alias ir = r4[8:0]
alias opd = r12[15:0]
alias acc = r5[8:0]
alias carry = r6[0:0]
alias x = r7[7:0]
alias y = r8[7:0]
alias sr = r9[7:0]
alias sp = r10[7:0]
alias mdr = r11[7:0]
alias ll = r100[7:0]
alias hh = r101[7:0]
###################################
macro d_read
    mov rd, 1
l0:
    jne dr, 1, l0
    mov rd, 0

macro pc_read
    mov mar, pc
    d_read

macro pc_read_inc
    add pc, pc, 1
    pc_read

macro imm_read
    pc_read_inc

macro abs_read
    pc_read_inc
    mov ll, mdr
    pc_read_inc
    mov hh, mdr

macro ind_read
    abs_read
    mov mar[0:7], ll
    mov mar[15:0], hh
    d_read

###################################
i_fetch:
    pc_read
    mov ir, mdr
    jmp i_decode
inc_pc:
    add pc, pc, 1
    jmp i_fetch
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
    abs_read
    mov pc[7:0], ll
    mov pc[15:8], hh
    jmp i_fetch
op_jmp_6C_ind:
    ind_read
    mov pc[7:0], ll
    mov pc[15:8], hh
    jmp i_fetch
