/* ROM: 0x80000000 - 0x8003FFFF, execute-only.
 * RAM: 0x80040000 - 0x8005FFFF, read/write.
 * GPIO: 0x80060000 - 0x8006000F, memory-mapped registers.
 */
ROM_ORIGIN = 0x80000000;
ROM_LENGTH = 0x40000;
RAM_ORIGIN = 0x80040000;
RAM_LENGTH = 0x20000;
GPIO_ORIGIN = 0x80060000;
GPIO_LENGTH = 0x10;

STACK_SIZE = 0x400;
NUM_HARTS = 1;

OUTPUT_ARCH("riscv")
ENTRY(_start)

MEMORY
{
    ROM (x)  : ORIGIN = ROM_ORIGIN, LENGTH = ROM_LENGTH
    RAM (rw) : ORIGIN = RAM_ORIGIN, LENGTH = RAM_LENGTH
    GPIO (rw) : ORIGIN = GPIO_ORIGIN, LENGTH = GPIO_LENGTH
}

PROVIDE(__stack_size = STACK_SIZE);
PROVIDE(__num_harts = NUM_HARTS);
PROVIDE(__gpio_base = ORIGIN(GPIO));

SECTIONS
{
    .text.init ORIGIN(ROM) :
    {
        *(.text.init)
    } > ROM

    .text.rvtest :
    {
        *(.text.rvtest)
        *(.text.rvtest.*)
    } > ROM

    .text.rvmodel :
    {
        *(.text.rvmodel)
        *(.text.rvmodel.*)
        *(.text)
        *(.text.*)
    } > ROM

    ASSERT(. <= ORIGIN(ROM) + LENGTH(ROM), "Program code exceeds ROM")

    /* Data reads cannot access the execute-only ROM. */
    .rodata :
    {
        . = ALIGN(4);
        *(.rodata)
        *(.rodata.*)
        *(.srodata)
        *(.srodata.*)
    } > RAM

    .data :
    {
        . = ALIGN(4);
        *(.data)
        *(.data.*)
        *(.sdata)
        *(.sdata.*)
    } > RAM

    .tohost : ALIGN(8)
    {
        KEEP(*(.tohost))
    } > RAM

    .bss (NOLOAD) :
    {
        . = ALIGN(4);
        __bss_start = .;
        *(.sbss)
        *(.sbss.*)
        *(.bss)
        *(.bss.*)
        *(COMMON)
        . = ALIGN(4);
        __bss_end = .;
    } > RAM

    .stack ORIGIN(RAM) + LENGTH(RAM) - __stack_size * __num_harts (NOLOAD) :
    {
        . = ALIGN(16);
        __stack_bottom = .;
        . += __stack_size * __num_harts;
        __stack_top = .;
    } > RAM

    _end = .;

    ASSERT(__bss_end <= __stack_bottom, "Data/BSS overlaps stack")
    ASSERT(__stack_top <= ORIGIN(RAM) + LENGTH(RAM), "Stack exceeds RAM")
}
