CROSS_COMPILE ?= riscv-none-elf-
GCC ?= $(CROSS_COMPILE)gcc
BUILD ?= build
LINKER_SCRIPT ?= link.ld

C_INCLUDE_DIR := ../hal/build/c-header
ASM_INCLUDE_DIR :=
STARTUP := startup.S

CFLAGS := -march=rv32i -mabi=ilp32 -nostdlib
DHRY_CFLAGS := -O3
ASFLAGS := $(CFLAGS)

C_SOURCES := $(wildcard tests/*.c)
NESTED_C_SOURCES := $(shell find tests -mindepth 2 -type f -name '*.c' -print)
C_HEADERS := $(shell find tests -type f -name '*.h' -print)
C_TEST_DIRS := $(sort $(dir $(NESTED_C_SOURCES)))
C_NESTED_TEST_NAMES := $(patsubst tests/%/,%,$(C_TEST_DIRS))
# A multi-file test may provide a linker script sized for its workload.
NESTED_LINKER_SCRIPT = $(or $(wildcard tests/$(1)/link.ld),$(LINKER_SCRIPT))
ASM_SOURCES := $(wildcard tests/*.S)

C_TARGETS := $(patsubst tests/%.c,$(BUILD)/%.elf,$(C_SOURCES)) \
	$(patsubst %,$(BUILD)/%.elf,$(C_NESTED_TEST_NAMES))
ASM_TARGETS := $(patsubst tests/%.S,$(BUILD)/%.elf,$(ASM_SOURCES))

.DEFAULT_GOAL := all

CALLER_MAKEFILE := $(abspath $(lastword $(MAKEFILE_LIST)))
CALLER_DIR := $(patsubst %/,%,$(dir $(CALLER_MAKEFILE)))
include ../common.mk

.PHONY: all clean

all: $(C_TARGETS) $(ASM_TARGETS)

# C tests
$(BUILD)/%.elf: tests/%.c $(C_HEADERS) $(STARTUP) $(LINKER_SCRIPT)
	@mkdir -p "$(BUILD)"
	$(call INFO,Building C test: $<)
	@{ $(GCC) $(CFLAGS) -I "$(C_INCLUDE_DIR)" \
		-T "$(LINKER_SCRIPT)" "$<" "$(STARTUP)" -o "$@" ; } \
		> "$(BUILD)/$*.log" 2>&1 \
		|| { cat "$(BUILD)/$*.log"; \
		     $(call ERROR,Failed to build C test: $<); exit 1; }
	$(call INFO,Successfully built: $@)

# A directory below tests/ is one multi-file C test.  Every C source directly
# in that directory is compiled and linked into a single ELF named after it.
define NESTED_C_TEST_RULE
$(BUILD)/$(1).elf: $$(filter tests/$(1)/%.c,$$(NESTED_C_SOURCES)) $$(C_HEADERS) $$(STARTUP) $(call NESTED_LINKER_SCRIPT,$(1))
	@mkdir -p "$$(dir $$@)"
	$$(call INFO,Building C test: $$@)
	@{ $$(GCC) $$(CFLAGS) $(if $(filter dhry,$(1)),$(DHRY_CFLAGS)) \
		-I "$$(C_INCLUDE_DIR)" -I "tests/$(1)" \
		-T "$(call NESTED_LINKER_SCRIPT,$(1))" $$(filter tests/$(1)/%.c,$$(NESTED_C_SOURCES)) "$$(STARTUP)" -o "$$@" ; } \
		> "$$(BUILD)/$(1).log" 2>&1 \
		|| { cat "$$(BUILD)/$(1).log"; \
		     $$(call ERROR,Failed to build C test: $$@); exit 1; }
	$$(call INFO,Successfully built: $$@)
endef

$(foreach test,$(C_NESTED_TEST_NAMES),$(eval $(call NESTED_C_TEST_RULE,$(test))))

# Assembly tests
$(BUILD)/%.elf: tests/%.S $(LINKER_SCRIPT)
	@mkdir -p "$(BUILD)"
	$(call INFO,Building ASM test: $<)
	@{ $(GCC) $(ASFLAGS) -I "$(ASM_INCLUDE_DIR)" \
		-T "$(LINKER_SCRIPT)" "$<" -o "$@" ; } \
		> "$(BUILD)/$*.log" 2>&1 \
		|| { cat "$(BUILD)/$*.log"; \
		     $(call ERROR,Failed to build ASM test: $<); exit 1; }
	$(call INFO,Successfully built: $@)

clean:
	$(call INFO,Cleaning build directory: $(BUILD))
	@build=$$(realpath -m -- "$(BUILD)"); \
	case "$$build" in \
		"$(CURDIR)"/*) ;; \
		*) printf '$(RED)[ERROR]$(RESET) Refusing to clean a build directory outside the code directory.\n' >&2; exit 1 ;; \
	esac; \
	rm -rf -- "$$build"
