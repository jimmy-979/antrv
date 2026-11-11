
/*
 * Memory map:
 *
 * ROM: 0x80000000 - 0x800003FF (execute-only)
 * RAM: 0x80040000 - 0x800403FF (read/write)
 * PERIPH: 0x80060000 - 0x8006000F (memory-mapped peripherals)
 */

ROM_ORIGIN = 0x80000000;
ROM_LENGTH = 0x400;

RAM_ORIGIN = 0x80040000;
RAM_LENGTH = 0x400;

PERIPH_ORIGIN = 0x80060000;
PERIPH_LENGTH = 0x18;

STACK_SIZE = 0x100;
NUM_HARTS = 1;

OUTPUT_ARCH("riscv")
ENTRY(_start)

MEMORY
{
    ROM    (x)  : ORIGIN = ROM_ORIGIN,    LENGTH = ROM_LENGTH
    RAM    (rw) : ORIGIN = RAM_ORIGIN,    LENGTH = RAM_LENGTH
    PERIPH (rw) : ORIGIN = PERIPH_ORIGIN, LENGTH = PERIPH_LENGTH
}

PROVIDE(__stack_size = STACK_SIZE);
PROVIDE(__num_harts = NUM_HARTS);
PROVIDE(__periph_base = ORIGIN(PERIPH));
PROVIDE(__periph_size = LENGTH(PERIPH));

SECTIONS
{
    /*
     * Code
     */
    .text.init ORIGIN(ROM) :
    {
        KEEP(*(.text.start))
        KEEP(*(.text.init))
        KEEP(*(.text.init.*))
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

    ASSERT(. <= ORIGIN(ROM) + LENGTH(ROM),
           "Program code exceeds ROM")

    /*
     * Read-only data
     *
     * Kept in RAM because ROM is execute-only.
     */
    .rodata :
    {
        . = ALIGN(4);
        *(.rodata)
        *(.rodata.*)
        *(.srodata)
        *(.srodata.*)
        . = ALIGN(4);
    } > RAM

    /*
     * Initialized data
     */
    .data :
    {
        . = ALIGN(4);
        __data_start = .;

        *(.data)
        *(.data.*)
        *(.sdata)
        *(.sdata.*)

        . = ALIGN(4);
        __data_end = .;
    } > RAM

    /*
     * HTIF / tohost
     */
    .tohost : ALIGN(8)
    {
        KEEP(*(.tohost))
    } > RAM

    /*
     * Uninitialized data
     */
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

    /*
     * Stack
     */
    .stack ORIGIN(RAM) + LENGTH(RAM) - __stack_size * __num_harts (NOLOAD) :
    {
        . = ALIGN(16);
        __stack_bottom = .;
        . += __stack_size * __num_harts;
        __stack_top = .;
    } > RAM

    _end = __bss_end;

    /*
     * Memory checks
     */
    ASSERT(__bss_end <= __stack_bottom,
           "Data/BSS overlaps stack")

    ASSERT(__stack_top <= ORIGIN(RAM) + LENGTH(RAM),
           "Stack exceeds RAM")

    ASSERT(SIZEOF(.text.init) +
           SIZEOF(.text.rvtest) +
           SIZEOF(.text.rvmodel) <= LENGTH(ROM),
           "Program code exceeds ROM")

    ASSERT(__data_end <= __stack_bottom,
           "Data overlaps stack")

    ASSERT(ADDR(.rodata) + SIZEOF(.rodata) <= __stack_bottom,
           "Read-only data exceeds available RAM")

    ASSERT(ADDR(.tohost) + SIZEOF(.tohost) <= __stack_bottom,
           "TOHOST exceeds available RAM")
}
