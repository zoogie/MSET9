	.arm
	.text
	.cpu arm946e-s
	.arch armv5te

#define GARBAGE 0x44444444

.global _start
start:


    @ldr sp, =0x22f18000
    @ldr r6, [sp, #0x44]
    adds r9, pc, #(1f - . - 8) @ trying to avoid
    rorne r8, r9, #16 @ encoding hell
    rorne r0, r8, #16
    svc 0x7b
1:
    msr cpsr_c, #(0x13 | (1 << 6) | (1 << 7)) @ SVC MODE | NO INTERRUPTS
    ldr r1, 1f
    mrc p15, 0, r4, c1, c0, 0
    and r4, r4, r1
    mcr p15, 0, r4, c1, c0, 0
    ldr pc, [sp,#0x4C]
1:
    .word ~((1 << 0) | (1 << 2) | (1 << 12))
2:
    @.word    0x25d48ae0
    @ .word    0x25c58bc0


.pool

