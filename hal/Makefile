
RDL ?= gpio.rdl
BUILD ?= build

CALLER_MAKEFILE := $(abspath $(lastword $(MAKEFILE_LIST)))
CALLER_DIR := $(patsubst %/,%,$(dir $(CALLER_MAKEFILE)))
include ../common.mk

# Usage: make [all | verilog | c-header | html | clean] RDL=gpio.rdl BUILD=build
# The verilog target also generates regblock/verilator.vlt for scoped lint waivers.

.DEFAULT_GOAL := all
.PHONY: all verilog c-header html clean

all: verilog c-header html

verilog:
	$(call INFO,Generating SystemVerilog from $(RDL))
	@mkdir -p "$(BUILD)/regblock"
	@{ peakrdl regblock "$(RDL)" -o "$(BUILD)/regblock/" \
		--default-reset arst_n --err-if-bad-addr --err-if-bad-rw; } \
		> "$(BUILD)/verilog.log" 2>&1 \
		|| { cat "$(BUILD)/verilog.log"; $(call ERROR,Failed to generate SystemVerilog); exit 1; }
	@{ \
		printf '%s\n' '`verilator_config'; \
		for source in "$(BUILD)/regblock/"*.sv; do \
			case "$$source" in \
				*_pkg.sv) \
					printf 'lint_off -rule UNUSEDPARAM -file "*%s"\n' "$$(basename "$$source")" ;; \
				*) \
					printf 'lint_off -rule MULTIDRIVEN -file "*%s"\n' "$$(basename "$$source")"; \
					printf 'lint_off -rule UNUSEDSIGNAL -file "*%s"\n' "$$(basename "$$source")" ;; \
			esac; \
		done; \
		printf '%s\n' 'lint_off -rule UNUSEDSIGNAL -file "*apb3_intf.sv"'; \
	} > "$(BUILD)/regblock/verilator.vlt"
	$(call INFO,SystemVerilog generation completed)

c-header:
	$(call INFO,Generating C header from $(RDL))
	@mkdir -p "$(BUILD)/c-header"
	@{ peakrdl c-header "$(RDL)" \
		-o "$(BUILD)/c-header/$(basename $(notdir $(RDL))).h" && \
		sed -i 's/__attribute__ ((__packed__))//g' \
		"$(BUILD)/c-header/$(basename $(notdir $(RDL))).h"; } \
		> "$(BUILD)/c-header.log" 2>&1 \
		|| { cat "$(BUILD)/c-header.log"; $(call ERROR,Failed to generate C header); exit 1; }
	$(call INFO,C header generation completed)

html:
	$(call INFO,Generating HTML documentation from $(RDL))
	@mkdir -p "$(BUILD)/html"
	@peakrdl html "$(RDL)" -o "$(BUILD)/html/" \
		> "$(BUILD)/html.log" 2>&1 \
		|| { cat "$(BUILD)/html.log"; $(call ERROR,Failed to generate HTML documentation); exit 1; }
	$(call INFO,HTML documentation generated)

clean:
	$(call INFO,Cleaning build directory: $(BUILD))
	@build=$$(realpath -m -- "$(BUILD)"); \
	case "$$build" in \
		"$(CURDIR)"/*) ;; \
		*) $(call ERROR,Refusing to clean a build directory outside the HAL directory); exit 1 ;; \
	esac; \
	rm -rf -- "$$build"
	$(call INFO,Clean completed)
