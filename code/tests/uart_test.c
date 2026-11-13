#include "drv_uart.h"

int main(void)
{
    while (1)
    {
        if (uart_rx_available())
        {
            char data = uart_getc();
            uart_putc(data);
        }
    }

    return 0;
}
