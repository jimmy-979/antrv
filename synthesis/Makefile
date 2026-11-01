PYTHON ?= python3
PARSER ?= ../python/parse_design.py
DESIGN ?= ../config/antrv_fpga.toml
TOP ?= $(shell $(PYTHON) $(PARSER) $(DESIGN) --field top)
SOURCES ?= $(shell $(PYTHON) $(PARSER) $(DESIGN) --field sources --root ..)
SDC ?= ../constraints/Go_Board_Clock_Constraint.sdc
PCF ?= ../constraints/Go_Board_Pin_Constraints.pcf
BUILD ?= build
ELF ?=

JSON := $(BUILD)/synth/$(TOP).json
ASC := $(BUILD)/pnr/$(TOP).asc
BIN := $(BUILD)/bitstream/$(TOP).bin
FIRMWARE_CONFIG := $(BUILD)/$(TOP).firmware.config

ifneq ($(strip $(ELF)),)
ROM_HEX := $(BUILD)/$(TOP).rom.hex
RAM_HEX := $(BUILD)/$(TOP).ram.hex
HEX_FILES := $(ROM_HEX) $(RAM_HEX)
SLANG_DEFINES := -D ANTRV_ROM_INIT_FILE=\"$(abspath $(ROM_HEX))\" \
	-D ANTRV_RAM_INIT_FILE=\"$(abspath $(RAM_HEX))\"
endif

.DEFAULT_GOAL := help

include ../common.mk

.PHONY: all synth pnr bits hex clean help FORCE

all: hal firmware
	@$(MAKE) bits

hex: $(HEX_FILES)
	@test -n "$(ELF)" || { echo "Set ELF=path/to/program.elf to generate memory hex files." >&2; exit 1; }

$(FIRMWARE_CONFIG): FORCE
	@mkdir -p $(BUILD)
	@printf '%s\n' '$(abspath $(ELF))' > "$@.tmp"
	@cmp -s "$@.tmp" "$@" || mv "$@.tmp" "$@"
	@rm -f "$@.tmp"

ifneq ($(strip $(ELF)),)
$(HEX_FILES) &: $(ELF) ../python/elf_to_hex.py $(FIRMWARE_CONFIG) Makefile
	@mkdir -p $(BUILD)
	@$(PYTHON) ../python/elf_to_hex.py "$(ELF)" \
		--rom "$(ROM_HEX)" --ram "$(RAM_HEX)"
endif

synth: $(JSON)
$(JSON): $(SOURCES) $(HAL_REG_BLOCK_FILES) Makefile $(FIRMWARE_CONFIG) $(HEX_FILES)
	@mkdir -p $(BUILD)/synth
	@yosys \
		-p "read_slang --top $(TOP) --ignore-assertions -I .. $(SLANG_DEFINES) $(SOURCES); \
		synth_ice40 -top $(TOP); \
		write_json $@" \
		> $(BUILD)/synth/$(TOP).synth.log 2>&1
	@$(PYTHON) ../python/yosys_stats.py $(BUILD)/synth/$(TOP).synth.log $(BUILD)/synth/$(TOP).synth.stats

pnr: $(ASC)
$(ASC): $(JSON)
	@mkdir -p $(BUILD)/pnr
	@nextpnr-ice40 --json $(JSON) \
                   --top $(TOP) \
                   --sdc $(SDC) \
                   --sdf $(BUILD)/pnr/$(TOP).sdf \
                   --hx1k \
                   --package vq100 \
                   --pcf $(PCF) \
                   --asc $(BUILD)/pnr/$(TOP).asc > $(BUILD)/pnr/$(TOP).pnr.log 2>&1
	@$(PYTHON) ../python/nextpnr_stats.py $(BUILD)/pnr/$(TOP).pnr.log $(BUILD)/pnr/$(TOP).pnr.stats;

bits: $(BIN)
$(BIN): $(ASC)
	@mkdir -p $(BUILD)/bitstream
	@icepack $(BUILD)/pnr/$(TOP).asc $(BUILD)/bitstream/$(TOP).bin

help:
	@echo "Usage: make [target] [ELF=path/to/program.elf]"
	@echo "Targets:"
	@echo "  all     - Rebuild HAL register block and code/build firmware, then synthesize and place and route"
	@echo "  hal     - Rebuild HAL register block"
	@echo "  firmware - Build code/build firmware"
	@echo "  synth   - Synthesize SystemVerilog directly (requires Yosys read_slang)"
	@echo "  pnr     - Place and route; print device utilization and save build/<top>.pnr.stats"
	@echo "  hex     - Generate ROM/RAM hex files from ELF (requires pyelftools)"
	@echo "  clean   - Remove build artifacts"
	@echo "  cleanall - Remove synthesis build artifacts, code/build, and hal/build"
	@echo ""
	@echo "Parameters:"
	@echo "  TOP     <- top module"
	@echo "  BUILD   <- build directory"
	@echo "  ELF     <- optional RV32 little-endian ELF; initializes ROM and RAM"
	@echo "             ROM: 0x80000000 + 0x40000 bytes; RAM: 0x80040000 + 0x20000 bytes"
	@echo "  PYTHON  <- Python interpreter (must have pyelftools when ELF is set)"
	@echo "             Example: make synth ELF=../code/build/gpio_test.elf PYTHON=../.venv/bin/python"

clean:
	@rm -rf $(BUILD)
