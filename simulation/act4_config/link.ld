/* ============================================================
 * DUT memory map
 *
 * ROM: execute-only
 *   0x80000000 - 0x800007FF  (256 KiB)
 *
 * RAM: read/write
 *   0x80000800 - 0x80000FFF  (128 KiB)
 * ============================================================ */

ROM_ORIGIN = 0x80000000;
ROM_LENGTH = 0x40000;      /* 256 KiB */

RAM_ORIGIN = 0x80040000;
RAM_LENGTH = 0x20000;      /* 128 KiB */

TEST_BASE = ROM_ORIGIN;

NUM_HARTS = 1;

/* Stack size: 1 KiB */
STACK_SIZE = 0x400;

OUTPUT_ARCH("riscv")
ENTRY(rvtest_entry_point)

MEMORY
{
    ROM (x)  : ORIGIN = ROM_ORIGIN, LENGTH = ROM_LENGTH
    RAM (rw) : ORIGIN = RAM_ORIGIN, LENGTH = RAM_LENGTH
}

PROVIDE(__stack_size = STACK_SIZE);
PROVIDE(__num_harts = NUM_HARTS);

SECTIONS
{
    /* ========================================================
     * ROM
     * ======================================================== */

    /*
     * Initial test entry point.
     */
    .text.init TEST_BASE :
    {
        *(.text.init)
    } > ROM

    /*
     * RISC-V architectural test code.
     */
    .text.rvtest :
    {
        *(.text.rvtest)
        *(.text.rvtest.*)
    } > ROM

    /*
     * Reference-model/test code and normal text.
     */
    .text.rvmodel :
    {
        *(.text.rvmodel)
        *(.text.rvmodel.*)
        *(.text)
        *(.text.*)
    } > ROM

    /*
     * Make sure all executable code fits in ROM.
     */
    ASSERT(
        . <= ORIGIN(ROM) + LENGTH(ROM),
        "Program code exceeds ROM"
    )


    /* ========================================================
     * RAM
     * ======================================================== */

    /*
     * Read-only data must be in RAM because the CPU cannot
     * perform data reads from the execute-only ROM.
     */
    .rodata :
    {
        . = ALIGN(4);

        *(.rodata)
        *(.rodata.*)
        *(.srodata)
        *(.srodata.*)
    } > RAM

    /*
     * Initialized writable data.
     */
    .data :
    {
        . = ALIGN(4);

        *(.data)
        *(.data.*)
        *(.sdata)
        *(.sdata.*)
    } > RAM

    /*
     * Zero-initialized data.
     */
    .bss :
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
     * Stack at the top of RAM.
     *
     * RISC-V stack grows downward.
     */
    .stack ORIGIN(RAM) + LENGTH(RAM) - __stack_size :
    {
        . = ALIGN(16);

        __stack_bottom = .;

        . += __stack_size * __num_harts;

        __stack_top = .;
    } > RAM

    /*
     * End of RAM allocations.
     */
    _end = .;


    /* ========================================================
     * Size checks
     * ======================================================== */

    ASSERT(
        __bss_end <= ORIGIN(RAM) + LENGTH(RAM),
        "Data/BSS exceeds RAM"
    )

    ASSERT(
        __stack_top <= ORIGIN(RAM) + LENGTH(RAM),
        "Stack exceeds RAM"
    )
}