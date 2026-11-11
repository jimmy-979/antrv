#include <stdint.h>
#include "uart.h"

#define UART_BASE 0x8006000C
#define UART ((volatile uart_reg_file_t *)UART_BASE)

int main(void)
{
    uint8_t data;

    while (1)
    {
        // Check whether a byte has been received
        if (UART->status & (1u << UART_REG_FILE__STATUS__RX_VALID_bp))
        {
            // Read received byte
            data = UART->rx_data & UART_REG_FILE__RX_DATA__DATA_bm;

            // Wait until transmitter is available
            while (UART->status & (1u << UART_REG_FILE__STATUS__TX_BUSY_bp))
            {
                // Wait
            }

            // Send received byte back
            UART->tx_data = data;
        }
    }

    return 0;
}
