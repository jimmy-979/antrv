TOP   ?= antrv_top
BUILD ?= build

PKG := $(wildcard ../rtl/*_pkg.sv)
RTL := $(filter-out $(PKG),$(wildcard ../rtl/*.sv))

SOURCES := $(PKG) $(RTL)

JSON := $(BUILD)/$(TOP).json

.DEFAULT_GOAL := help

.PHONY: all synth clean help

all: synth

synth: $(JSON)

$(JSON): $(SOURCES)
	@mkdir -p $(BUILD)
	@yosys \
		-p "read_verilog -sv $(SOURCES); \
		hierarchy -top $(TOP); \
		synth_ice40 -top $(TOP); \
		write_json $@" \
		> $(BUILD)/$(TOP).synth.log 2>&1
	@python3 yosys_stats.py \
		$(BUILD)/$(TOP).synth.log \
		$(BUILD)/$(TOP).synth.stats

help:
	@echo "Usage: make [target]"
	@echo "Targets:"
	@echo "  synth   - Synthesize the design"
	@echo "  clean   - Remove build artifacts"

clean:
	@rm -rf $(BUILD)