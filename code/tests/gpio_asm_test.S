    .equ GPIO_BASE,      0x80060000
    .equ GPIO_DATA_IN,   0x00
    .equ GPIO_DATA_OUT,  0x04
    .equ GPIO_DIRECTION, 0x08

    .section .text
    .globl _start
_start:
    li t0, GPIO_BASE

    sw zero, GPIO_DATA_OUT(t0)

    li t1, 0xf0
    sw t1, GPIO_DIRECTION(t0)

monitor_gpio:
    lw t1, GPIO_DATA_IN(t0)
    andi t1, t1, 0x0f
    slli t1, t1, 4
    sw t1, GPIO_DATA_OUT(t0)
    j monitor_gpio
