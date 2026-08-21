    .section .trampoline,"ax"
    .align 2
    .global _avsp_trampoline_start
    .global _avsp_trampoline_end

_avsp_trampoline_start:
    mov     r5,r7
    mov     #0,r0
1:
    cmp/eq  r0,r6
    bt      2f
    mov.b   @r4+,r1
    mov.b   r1,@r5
    add     #1,r5
    add     #-1,r6
    bra     1b
    nop
2:
    mov.l   3f,r1
    mov     #0x10,r0
    mov.b   r0,@r1
    mov     #1,r0
    mov.b   r0,@r1
    jmp     @r7
    nop
    .align 2
3:
    .long   0xfffffe92
_avsp_trampoline_end:
