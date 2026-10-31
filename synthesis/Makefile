PYTHON ?= python3
PARSER ?= ../python/parse_design.py
DESIGN ?= ../config/antrv.toml
TOP ?= $(shell $(PYTHON) $(PARSER) $(DESIGN) --field top)
SOURCES ?= $(shell $(PYTHON) $(PARSER) $(DESIGN) --field sources --root ..)
BUILD ?= build

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
	@python3 ../python/yosys_stats.py \
		$(BUILD)/$(TOP).synth.log \
		$(BUILD)/$(TOP).synth.stats

help:
	@echo "Usage: make [target]"
	@echo "Targets:"
	@echo "  synth   - Synthesize the design"
	@echo "  clean   - Remove build artifacts"
	@echo ""
	@echo "Parameters:"
	@echo "  TOP     <- top module"
	@echo "  BUILD   <- build directory"

clean:
	@rm -rf $(BUILD)