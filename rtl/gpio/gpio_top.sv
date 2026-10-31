module gpio_top #(
    parameter int GPIO_WIDTH = gpio_reg_file_pkg::GPIO_WIDTH
) (
    input logic                            clk_i,
    input logic                            rst_n_i,
          apb3_intf.slave                  s_apb,
    inout logic           [GPIO_WIDTH-1:0] gpio_pins_io
);

  gpio_reg_file_pkg::gpio_reg_file__in_t  hwif_in;
  gpio_reg_file_pkg::gpio_reg_file__out_t hwif_out;

  initial begin
    assert (GPIO_WIDTH == gpio_reg_file_pkg::GPIO_WIDTH)
        else $fatal(1, "GPIO_WIDTH must match the generated register block");
  end

  assign hwif_in.data_in.pin.next = gpio_pins_io;

  for (genvar pin = 0; pin < GPIO_WIDTH; pin++) begin : gen_gpio_pins
    assign gpio_pins_io[pin] = hwif_out.direction.pin.value[pin] ?
                                    hwif_out.data_out.pin.value[pin] :
                                    1'bz;
  end

  gpio_reg_file u_gpio_reg_file (
      .clk     (clk_i),
      .arst_n  (rst_n_i),
      .s_apb   (s_apb),
      .hwif_in (hwif_in),
      .hwif_out(hwif_out)
  );
endmodule
