module tb_antrv #(
    parameter int GPIO_WIDTH = gpio_reg_file_pkg::GPIO_WIDTH
) ();

  logic                  clk;
  logic                  rst_n;
  logic [GPIO_WIDTH-1:0] gpio_drive_data;
  logic [GPIO_WIDTH-1:0] gpio_drive_enable;
  logic [GPIO_WIDTH-1:0] gpio_pins;

  for (genvar pin = 0; pin < GPIO_WIDTH; pin++) begin : gen_gpio_drive
    assign gpio_pins[pin] = gpio_drive_enable[pin] ? gpio_drive_data[pin] : 1'bz;
  end

  antrv_top #(
      .GPIO_WIDTH(GPIO_WIDTH)
  ) inst_antrv (
      .clk_i       (clk),
      .rst_n_i     (rst_n),
      .gpio_pins_io(gpio_pins)
  );

endmodule
