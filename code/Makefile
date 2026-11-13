
CROSS_COMPILE ?= riscv-none-elf-
GCC ?= $(CROSS_COMPILE)gcc

BUILD ?= build
LINKER_SCRIPT ?= link.ld

C_INCLUDE_DIR := ../hal/build/c-header
DRIVERS_DIR := drivers
RUNTIME_DIR := runtime

ASM_INCLUDE_DIR :=
STARTUP := startup.S

# Compiler flags
CFLAGS := -march=rv32i -mabi=ilp32
DHRY_CFLAGS := -O3 -DTIME
ASFLAGS := $(CFLAGS)

# Linker flags and libraries
LDFLAGS := -nostartfiles
LDLIBS := -lc -lm -lgcc

# Test sources
C_SOURCES := $(wildcard tests/*.c)
NESTED_C_SOURCES := $(shell find tests -mindepth 2 -type f -name '*.c' -print)
C_HEADERS := $(shell find tests -type f -name '*.h' -print)

C_TEST_DIRS := $(sort $(dir $(NESTED_C_SOURCES)))
C_NESTED_TEST_NAMES := $(patsubst tests/%/,%,$(C_TEST_DIRS))

# A multi-file test may provide a linker script sized for its workload.
NESTED_LINKER_SCRIPT = $(or $(wildcard tests/$(1)/link.ld),$(LINKER_SCRIPT))

ASM_SOURCES := $(wildcard tests/*.S)

# Driver sources and include directories
DRIVER_SOURCES := $(shell find $(DRIVERS_DIR) -type f -name '*.c' -print)
DRIVER_HEADERS := $(shell find $(DRIVERS_DIR) -type f -name '*.h' -print)
DRIVER_INCLUDE_DIRS := $(sort $(dir $(DRIVER_HEADERS)))
DRIVER_INCLUDE_FLAGS := $(addprefix -I,$(DRIVER_INCLUDE_DIRS))

# Runtime sources (e.g. syscalls.c)
RUNTIME_SOURCES := $(shell find $(RUNTIME_DIR) -type f -name '*.c' -print)
RUNTIME_HEADERS := $(shell find $(RUNTIME_DIR) -type f -name '*.h' -print)
RUNTIME_INCLUDE_DIRS := $(sort $(dir $(RUNTIME_HEADERS)))
RUNTIME_INCLUDE_FLAGS := $(addprefix -I,$(RUNTIME_INCLUDE_DIRS))

# Common include flags
INCLUDE_FLAGS := -I"$(C_INCLUDE_DIR)" $(DRIVER_INCLUDE_FLAGS) $(RUNTIME_INCLUDE_FLAGS)

# Targets
C_TARGETS := $(patsubst tests/%.c,$(BUILD)/%.elf,$(C_SOURCES)) \
             $(patsubst %,$(BUILD)/%.elf,$(C_NESTED_TEST_NAMES))

ASM_TARGETS := $(patsubst tests/%.S,$(BUILD)/%.elf,$(ASM_SOURCES))

.DEFAULT_GOAL := all

CALLER_MAKEFILE := $(abspath $(lastword $(MAKEFILE_LIST)))
CALLER_DIR := $(patsubst %/,%,$(dir $(CALLER_MAKEFILE)))
include ../common.mk

.PHONY: all clean

all: $(C_TARGETS) $(ASM_TARGETS)

# All common C sources linked into every C test
COMMON_C_SOURCES := $(DRIVER_SOURCES) $(RUNTIME_SOURCES)

# C tests directly under tests/
$(BUILD)/%.elf: tests/%.c $(C_HEADERS) $(DRIVER_HEADERS) $(RUNTIME_HEADERS) \
                $(COMMON_C_SOURCES) $(STARTUP) $(LINKER_SCRIPT)
	@mkdir -p "$(dir $@)"
	$(call INFO,Building C test: $<)
	@{ $(GCC) $(CFLAGS) $(INCLUDE_FLAGS) \
		-T "$(LINKER_SCRIPT)" \
		"$<" $(COMMON_C_SOURCES) "$(STARTUP)" \
		$(LDFLAGS) $(LDLIBS) -o "$@" ; } \
		> "$(BUILD)/$*.log" 2>&1 \
		|| { cat "$(BUILD)/$*.log"; \
		     $(call ERROR,Failed to build C test: $<); exit 1; }
	$(call INFO,Successfully built: $@)

# Nested multi-file C tests
define NESTED_C_TEST_RULE
$(BUILD)/$(1).elf: $$(filter tests/$(1)/%.c,$$(NESTED_C_SOURCES)) \
                   $$(C_HEADERS) $$(DRIVER_HEADERS) $$(RUNTIME_HEADERS) \
                   $$(COMMON_C_SOURCES) $$(STARTUP) \
                   $(call NESTED_LINKER_SCRIPT,$(1))
	@mkdir -p "$$(dir $$@)"
	$$(call INFO,Building C test: $$@)
	@{ $$(GCC) $$(CFLAGS) \
		$$(if $$(filter dhry,$(1)),$$(DHRY_CFLAGS)) \
		$$(INCLUDE_FLAGS) -I "tests/$(1)" \
		-T "$(call NESTED_LINKER_SCRIPT,$(1))" \
		$$(filter tests/$(1)/%.c,$$(NESTED_C_SOURCES)) \
		$$(COMMON_C_SOURCES) "$$(STARTUP)" \
		$$(LDFLAGS) $$(LDLIBS) -o "$$@" ; } \
		> "$$(BUILD)/$(1).log" 2>&1 \
		|| { cat "$$(BUILD)/$(1).log"; \
		     $$(call ERROR,Failed to build C test: $$@); exit 1; }
	$$(call INFO,Successfully built: $$@)
endef

$(foreach test,$(C_NESTED_TEST_NAMES),$(eval $(call NESTED_C_TEST_RULE,$(test))))

# Assembly tests
$(BUILD)/%.elf: tests/%.S $(LINKER_SCRIPT)
	@mkdir -p "$(dir $@)"
	$(call INFO,Building ASM test: $<)
	@{ $(GCC) $(ASFLAGS) -I "$(ASM_INCLUDE_DIR)" \
		-T "$(LINKER_SCRIPT)" "$<" \
		$(LDFLAGS) $(LDLIBS) -o "$@" ; } \
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
