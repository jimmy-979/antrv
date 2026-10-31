RDL ?= gpio.rdl
BUILD ?= build

# Usage: make [all | verilog | c-header | html | clean] RDL=gpio.rdl BUILD=build
# The verilog target also generates regblock/verilator.vlt for scoped lint waivers.
.PHONY: all verilog c-header html clean

all: verilog c-header html

verilog:
	@peakrdl regblock "$(RDL)" -o "$(BUILD)/regblock/" --default-reset arst_n \
		--err-if-bad-addr --err-if-bad-rw
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

c-header:
	@mkdir -p "$(BUILD)/c-header"
	@peakrdl c-header "$(RDL)" -o "$(BUILD)/c-header/$(basename $(notdir $(RDL))).h"

html:
	@peakrdl html "$(RDL)" -o "$(BUILD)/html/"

clean:
	@build=$$(realpath -m -- "$(BUILD)"); \
	case "$$build" in \
		"$(CURDIR)"/*) ;; \
		*) printf '%s\n' "Refusing to clean a build directory outside the hal directory." >&2; exit 1 ;; \
	esac; \
	rm -rf -- "$$build"