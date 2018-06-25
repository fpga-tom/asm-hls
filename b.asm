l0:
    add r11, r10, r8
    add r10, r9, r7
    add r9, r5, r6
    mul r8, r4, 4
    mul r7, r3, 3
    mul r6, r2, 2
    mul r5, r1, 1
    mov r4, r3
    mov r3, r2
    mov r2, r1
    mov r1, r0
    jmp l0
