# Shared targets for Makefiles run from synthesis/ or simulation/.
# HAL builds generate only the register block and Verilator configuration.
HAL_REG_BLOCK_FILES := ../hal/build/regblock/gpio_reg_file.sv \
	../hal/build/regblock/gpio_reg_file_pkg.sv ../hal/build/regblock/verilator.vlt

.PHONY: hal firmware cleanall

hal:
	@$(MAKE) -C ../hal BUILD=build verilog

firmware:
	@$(MAKE) -C ../code BUILD=build all

$(HAL_REG_BLOCK_FILES) &: ../hal/gpio.rdl ../hal/Makefile
	@$(MAKE) -C ../hal BUILD=build verilog

cleanall: clean
	@$(MAKE) -C ../code BUILD=build clean
	@$(MAKE) -C ../hal BUILD=build clean
