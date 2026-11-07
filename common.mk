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
	@$(MAKE) -C ../code BUILD=build all

$(HAL_REG_BLOCK_FILES) &: ../hal/gpio.rdl ../hal/uart.rdl ../hal/Makefile
	@for rdl in gpio.rdl uart.rdl; do \
		$(MAKE) -C ../hal RDL=$$rdl BUILD=build verilog; \
	done

cleanall: clean
	@$(MAKE) -C ../code BUILD=build clean
	@$(MAKE) -C ../hal BUILD=build clean
