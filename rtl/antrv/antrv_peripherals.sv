module antrv_peripherals #(
    parameter logic [31:0] BASE_ADDR  = 32'h80060000,
    parameter int          GPIO_WIDTH = gpio_reg_file_pkg::GPIO_WIDTH,
    parameter int          BAUD_RATE  = 115200,
    parameter int          CLOCK_FREQ = 25_000_000
) (
    input  logic                            clk_i,
    input  logic                            rst_n_i,
           apb3_intf.slave                  s_apb,
    inout  wire            [GPIO_WIDTH-1:0] gpio_pins_io,
    input  logic                            uart_rx_i,
    output logic                            uart_tx_o
);

  localparam logic [31:0] GpioBaseAddr = BASE_ADDR;
  localparam logic [31:0] UartBaseAddr = BASE_ADDR + gpio_reg_file_pkg::GPIO_REG_FILE_SIZE;

  localparam int IdGpio = 0;
  localparam int IdUart = 1;

  apb3_intf peripheral_apb[0:1] (
      .PCLK   (clk_i),
      .PRESETn(rst_n_i)
  );

  antrv_apb3_decoder #(
      .N        (2),
      .BASE_ADDR('{GpioBaseAddr, UartBaseAddr}),
      .SIZE     ('{gpio_reg_file_pkg::GPIO_REG_FILE_SIZE, uart_reg_file_pkg::UART_REG_FILE_SIZE})
  ) inst_apb_decoder (
      .m_apb(s_apb),
      .s_apb(peripheral_apb)
  );

  gpio_top #(
      .GPIO_WIDTH(GPIO_WIDTH)
  ) inst_gpio (
      .clk_i       (clk_i),
      .rst_n_i     (rst_n_i),
      .s_apb       (peripheral_apb[IdGpio]),
      .gpio_pins_io(gpio_pins_io)
  );

  uart_top #(
      .BAUD_RATE (BAUD_RATE),
      .CLOCK_FREQ(CLOCK_FREQ)
  ) inst_uart (
      .clk_i  (clk_i),
      .rst_n_i(rst_n_i),
      .s_apb  (peripheral_apb[IdUart]),
      .rx_i   (uart_rx_i),
      .tx_o   (uart_tx_o)
  );

endmodule
