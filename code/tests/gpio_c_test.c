#include <stdint.h>
// #include "gpio.h"

typedef struct
{
    uint32_t data_in;
    uint32_t data_out;
    uint32_t direction;
} gpio_regs_t;

#define GPIO_BASE 0x80180000
#define GPIO ((volatile gpio_regs_t *)GPIO_BASE)

void main(void)
{
    GPIO->data_out = 0x00;
    GPIO->direction = 0xf0;

    while (1)
    {
        uint32_t input = GPIO->data_in & 0x0f;
        GPIO->data_out = input << 4;
    }
}