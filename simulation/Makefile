# Usage: make -C simulation [-j N] [help | all | generate | regenerate | list-tests | status | test-<name> | status-<name> | sim | lint | clean]
# Use -k to continue running other tests after a failure.
# Regression output is saved in $(SIM_BUILD)/test-<name>/simulation.log.
# The Verilator executable is compiled once in $(SIM_BUILD)/simulator and shared.
# Completed results are reused; pass RERUN=1 to force fresh simulations.
# Use 'make html' to create a selectable status report in $(SIM_BUILD)/regression.html.
# 'all' and 'sim' display live completion counts and elapsed time.
# Multiple test targets show summaries; single tests also stream their full logs.
PYTHON ?= python
VERILATOR ?= verilator
COCOTB_TEST_MODULES ?= antrv_top_test
WAVES ?= 1
EXTRA_ARGS ?= -Wall --trace --trace-fst --trace-structs
SIM_BUILD ?= build
DESIGN ?= ../config/antrv.toml
PARSER ?= ../python/parse_design.py
REG_BLOCK_FILES = ../hal/build/regblock/gpio_reg_file.sv ../hal/build/regblock/gpio_reg_file_pkg.sv ../hal/build/regblock/verilator.vlt
COMPILE_ARGS += $(abspath ../hal/build/regblock/verilator.vlt)
export PYTHON COCOTB_TEST_MODULES WAVES EXTRA_ARGS SIM_BUILD DESIGN PARSER COMPILE_ARGS
ifneq ($(word 2,$(filter test-%,$(MAKECMDGOALS))),)
export LOG_TEST_OUTPUT ?= 1
endif

TEST_FILE ?= $(COCOTB_TEST_MODULES).py
GENERATED_MAKEFILE ?= build/regression.mk

.DEFAULT_GOAL := all
.PHONY: help all generate regenerate list-tests status html sim lint clean

help:
	@printf '%s\n' \
		'Simulation targets:' \
		'  all              Run the complete regression (default).' \
		'  generate         Generate the regression makefile if missing.' \
		'  regenerate       Regenerate the regression makefile.' \
		'  list-tests       List available regression tests.' \
		'  test-<name>      Run one regression test.' \
		'  status           Show status for all regression tests.' \
		'  status-<name>    Show status for one regression test.' \
		'  html             Generate the selectable regression report.' \
		'  lint             Run Verilator lint.' \
		'  clean            Remove simulation build and result files.' \
		'' \
		'Options:' \
		'  RERUN=1          Rerun tests instead of reusing completed results.' \
		'  SIM_BUILD=path   Set the simulation build directory.' \
		'  DESIGN=path      Set the design TOML configuration.'

generate: $(GENERATED_MAKEFILE) $(REG_BLOCK_FILES)

$(REG_BLOCK_FILES) &: ../hal/gpio.rdl ../hal/Makefile
	+$(MAKE) -C ../hal verilog

# Regenerate when the generator or test module changes.
$(GENERATED_MAKEFILE): ../python/list_tests.py $(TEST_FILE)
	@$(PYTHON) ../python/list_tests.py "$(TEST_FILE)" --output "$(GENERATED_MAKEFILE)"

regenerate:
	@$(PYTHON) ../python/list_tests.py "$(TEST_FILE)" --output "$(GENERATED_MAKEFILE)"

all: generate
	+@$(PYTHON) ../python/regression_progress.py --make "$(MAKE)" --makefile "$(GENERATED_MAKEFILE)"

list-tests: generate
	+$(MAKE) -f "$(GENERATED_MAKEFILE)" list-tests

html: generate
	+@$(MAKE) --no-print-directory -f "$(GENERATED_MAKEFILE)" html

status:
	@test -f "$(GENERATED_MAKEFILE)" || { printf '\033[31m%s\033[0m\n' "No generated regression makefile. Run 'make generate' first." >&2; exit 1; }
	+$(MAKE) -f "$(GENERATED_MAKEFILE)" status

status-%:
	@test -f "$(GENERATED_MAKEFILE)" || { printf '\033[31m%s\033[0m\n' "No generated regression makefile. Run 'make generate' first." >&2; exit 1; }
	+$(MAKE) -f "$(GENERATED_MAKEFILE)" $@

test-%: generate
	+$(MAKE) -f "$(GENERATED_MAKEFILE)" $@

sim: all

lint: $(REG_BLOCK_FILES)
	@$(VERILATOR) --lint-only -Wall \
		$(COMPILE_ARGS) \
		--top-module "$$($(PYTHON) "$(PARSER)" "$(DESIGN)" --field top)" \
		$$($(PYTHON) "$(PARSER)" "$(DESIGN)" --field sources --root ..)

clean:
	@build=$$(realpath -m -- "$(SIM_BUILD)"); \
	case "$$build" in \
		"$(CURDIR)"/*) ;; \
		*) printf '\033[31m%s\033[0m\n' "Refusing to clean a build directory outside the simulation directory." >&2; exit 1 ;; \
	esac; \
	rm -rf -- "$$build"
	@rm -f -- "$(GENERATED_MAKEFILE)" results.xml dump.fst dump.vcd
