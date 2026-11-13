
#include "drv_uart.h"
#include "uart.h"

/* UART register interface */
#define UART ((volatile uart_reg_file_t *)UART_BASE_ADDR)

/*
 * Transmit a single character.
 *
 * Blocks until the UART is ready to accept another character.
 */
void uart_putc(char c)
{
    while (UART->status & UART_REG_FILE__STATUS__TX_BUSY_bm)
    {
        /* Wait for transmitter */
    }

    UART->tx_data = (uint8_t)c;
}

/*
 * Transmit a null-terminated string.
 */
void uart_puts(const char *str)
{
    while (*str)
    {
        uart_putc(*str++);
    }
}

/*
 * Check whether a received character is available.
 */
bool uart_rx_available(void)
{
    return (UART->status & UART_REG_FILE__STATUS__RX_VALID_bm) != 0;
}

/*
 * Receive a single character.
 *
 * Blocks until a character is received.
 */
char uart_getc(void)
{
    while (!uart_rx_available())
    {
        /* Wait for received character */
    }

    return (char)(UART->rx_data & UART_REG_FILE__RX_DATA__DATA_bm);
}
