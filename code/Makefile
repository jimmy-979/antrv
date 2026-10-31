CROSS_COMPILE ?= riscv-none-elf-
GCC ?= $(CROSS_COMPILE)gcc
BUILD ?= build
LINKER_SCRIPT ?= link.ld

# Usage: make [all | clean] BUILD=build CROSS_COMPILE=riscv-none-elf-
.DEFAULT_GOAL := all
.PHONY: all clean

all: $(BUILD)/gpio_test.elf

$(BUILD)/gpio_test.elf: tests/gpio_test.S $(LINKER_SCRIPT) ../simulation/act4_config/rvmodel_macros.h Makefile
	@mkdir -p "$(BUILD)"
	$(GCC) -march=rv32i -mabi=ilp32 -nostdlib \
		-I ../simulation/act4_config \
		-T "$(LINKER_SCRIPT)" "$<" -o "$@"

clean:
	@build=$$(realpath -m -- "$(BUILD)"); \
	case "$$build" in \
		"$(CURDIR)"/*) ;; \
		*) printf '%s\n' "Refusing to clean a build directory outside the code directory." >&2; exit 1 ;; \
	esac; \
	rm -rf -- "$$build"
