#include "drv_uart.h"

#include <stddef.h>
#include <stdint.h>

int _write(int fd, const char *buf, int len)
{
    (void)fd;

    for (int i = 0; i < len; i++)
    {
        uart_putc(buf[i]);
    }

    return len;
}

extern char _end;
extern char __stack_bottom;

static uintptr_t heap_end;

void *_sbrk(ptrdiff_t increment)
{
    if (heap_end == 0)
    {
        heap_end = (uintptr_t)&_end;
    }

    uintptr_t limit = (uintptr_t)&__stack_bottom;
    if (heap_end > limit || increment < 0 ||
        (uintptr_t)increment > limit - heap_end)
    {
        return (void *)(intptr_t)-1;
    }

    uintptr_t previous_heap_end = heap_end;
    heap_end += (uintptr_t)increment;
    return (void *)previous_heap_end;
}
