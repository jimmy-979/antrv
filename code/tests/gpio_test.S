#include "rvmodel_macros.h"

    .equ GPIO_BASE,      0x80060000
    .equ GPIO_DATA_OUT,  0x04
    .equ GPIO_DIRECTION, 0x08

    .section .text
    .globl _start
_start:
    li t0, GPIO_BASE

    # Preload GPIO[3:0] = 1 0 1 0 before enabling the output drivers.
    li t1, 0x0a
    sw t1, GPIO_DATA_OUT(t0)

    li t1, 0x0f
    sw t1, GPIO_DIRECTION(t0)

    RVMODEL_HALT_PASS

    RVMODEL_DATA_SECTION
