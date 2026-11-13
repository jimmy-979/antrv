BLUE  := \033[34m
RED   := \033[31m
RESET := \033[0m

INFO  = @printf '$(BLUE)[$(notdir $(CALLER_DIR))]$(RESET) %s\n' "$(1)"
ERROR = printf '$(RED)[$(notdir $(CALLER_DIR))]$(RESET) %s\n' "$(1)" >&2

# Shared targets for Makefiles run from synthesis/ or simulation/.
# HAL builds generate only the register block and Verilator configuration.
HAL_REG_BLOCK_FILES := ../hal/build/regblock/gpio_reg_file.sv \
                       ../hal/build/regblock/gpio_reg_file_pkg.sv \
                       ../hal/build/regblock/uart_reg_file.sv \
                       ../hal/build/regblock/uart_reg_file_pkg.sv \
                       ../hal/build/regblock/verilator.vlt

.PHONY: hal firmware cleanall

hal: $(HAL_REG_BLOCK_FILES)

firmware:
	@for rdl in gpio.rdl uart.rdl; do \
		$(MAKE) -C ../hal RDL=$$rdl BUILD=build c-header; \
	done
	@$(MAKE) -C ../code BUILD=build all

$(HAL_REG_BLOCK_FILES) &: ../hal/gpio.rdl ../hal/uart.rdl
	@for rdl in gpio.rdl uart.rdl; do \
		$(MAKE) -C ../hal RDL=$$rdl BUILD=build verilog; \
	done

cleanall: clean
	@$(MAKE) -C ../code BUILD=build clean
	@$(MAKE) -C ../hal BUILD=build clean
