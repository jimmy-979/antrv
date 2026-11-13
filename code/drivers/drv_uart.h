
#ifndef UART_DRIVER_H
#define UART_DRIVER_H

#include <stdbool.h>
#include <stdint.h>

/*
 * UART driver configuration.
 * Override UART_BASE_ADDR through your build configuration.
 */
#ifndef UART_BASE_ADDR
#define UART_BASE_ADDR 0x8018000C
#endif

void uart_putc(char c);
void uart_puts(const char *str);

bool uart_rx_available(void);
char uart_getc(void);

#endif /* UART_DRIVER_H */
