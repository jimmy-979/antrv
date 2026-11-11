`ifndef ANTRV_ROM_INIT_FILE
`define ANTRV_ROM_INIT_FILE ""
`endif

`ifndef ANTRV_RAM_INIT_FILE
`define ANTRV_RAM_INIT_FILE ""
`endif

module antrv_top #(
    parameter int           ROM_ADDR_WIDTH   = $clog2(32'h40000),
    parameter int           RAM_ADDR_WIDTH   = $clog2(32'h20000),
    // Peripheral address map
    parameter logic  [31:0] PERIPH_BASE_ADDR = 32'h80060000,
    // Peripheral configuration
    parameter int           GPIO_WIDTH       = gpio_reg_file_pkg::GPIO_WIDTH,
    parameter int           BAUD_RATE        = 115200,
    parameter int           CLOCK_FREQ       = 25_000_000,
    // Memory initialization files
    parameter string        ROM_INIT_FILE    = `ANTRV_ROM_INIT_FILE,
    parameter string        RAM_INIT_FILE    = `ANTRV_RAM_INIT_FILE
) (
    input logic                  clk_i,
    input logic                  rst_n_i,
    // GPIO
    inout wire  [GPIO_WIDTH-1:0] gpio_pins_io
);

  localparam logic [31:0] GpioBaseAddr = PERIPH_BASE_ADDR;
  localparam logic [31:0] GpioSize     = 32'h0000000C;
  localparam logic [31:0] UartBaseAddr = GpioBaseAddr + GpioSize;
  localparam logic [31:0] UartSize     = 32'h0000000C;

  localparam int          IdGpio       = 0;
  localparam int          IdUart       = 1;

  // ------------------------------------------------------------
  // CPU / Memory signals
  // ------------------------------------------------------------

  logic [ROM_ADDR_WIDTH-1:0] rom_addr;
  logic [              31:0] instr;

  logic                      ram_we;
  logic [               3:0] ram_wmask;
  logic [RAM_ADDR_WIDTH-1:0] ram_addr;
  logic [              31:0] ram_wdata;
  logic [              31:0] ram_rdata;

  logic                      cpu_we;
  logic                      cpu_req;
  logic [              31:0] cpu_byte_addr;
  logic [              31:0] cpu_rdata;
  logic                      cpu_ready;

  // ------------------------------------------------------------
  // Peripheral selection / response
  // ------------------------------------------------------------

  logic                      peripheral_selected;
  logic                      peripheral_ready;
  logic [              31:0] peripheral_rdata;
  logic                      unused_peripheral_error;

  logic                      cpu_using_peripheral;
  logic [              31:0] peripheral_read_result;

  // ------------------------------------------------------------
  // APB interfaces
  // ------------------------------------------------------------

  apb3_intf cpu_apb (
      .PCLK   (clk_i),
      .PRESETn(rst_n_i)
  );

  apb3_intf peripheral_apb[0:1] (
      .PCLK(clk_i),
      .PRESETn(rst_n_i)
  );

  // ------------------------------------------------------------
  // Address decoding
  // ------------------------------------------------------------

  assign peripheral_selected =
      (cpu_byte_addr >= GpioBaseAddr &&
       cpu_byte_addr < GpioBaseAddr + GpioSize) ||
      (cpu_byte_addr >= UartBaseAddr &&
       cpu_byte_addr < UartBaseAddr + UartSize);

  // ------------------------------------------------------------
  // RAM interface
  // ------------------------------------------------------------

  assign ram_addr = {2'b00, cpu_byte_addr[RAM_ADDR_WIDTH-1:2]};

  assign ram_we = cpu_we && !peripheral_selected;

  // ------------------------------------------------------------
  // CPU response mux
  // ------------------------------------------------------------

  assign cpu_ready = peripheral_selected ? peripheral_ready : 1'b1;

  assign cpu_rdata = cpu_using_peripheral ? peripheral_read_result : ram_rdata;

  always_ff @(posedge clk_i or negedge rst_n_i) begin
    if (!rst_n_i) begin
      cpu_using_peripheral   <= 1'b0;
      peripheral_read_result <= 32'b0;
    end else begin
      if (cpu_req) begin
        cpu_using_peripheral <= peripheral_selected;
      end

      if (peripheral_ready) begin
        peripheral_read_result <= peripheral_rdata;
      end
    end
  end

  // ------------------------------------------------------------
  // CPU
  // ------------------------------------------------------------

  antrv_cpu #(
      .IMEM_ADDR_WIDTH(ROM_ADDR_WIDTH)
  ) inst_cpu (
      .clk_i  (clk_i),
      .rst_n_i(rst_n_i),

      .imem_addr_o(rom_addr),
      .imem_data_i(instr),

      .dmem_we_o   (cpu_we),
      .dmem_wmask_o(ram_wmask),
      .dmem_addr_o (cpu_byte_addr),
      .dmem_wdata_o(ram_wdata),
      .dmem_rdata_i(cpu_rdata),
      .dmem_req_o  (cpu_req),
      .dmem_ready_i(cpu_ready)
  );

  // ------------------------------------------------------------
  // ROM
  // ------------------------------------------------------------

  antrv_mem #(
      .ADDR_WIDTH(ROM_ADDR_WIDTH),
      .DATA_WIDTH(32),
      .INIT_FILE (ROM_INIT_FILE)
  ) inst_rom (
      .wclk_i (clk_i),
      .rclk_i (clk_i),
      .we_i   (1'b0),
      .wmask_i(4'b0000),
      .waddr_i({ROM_ADDR_WIDTH{1'b0}}),
      .wdata_i(32'b0),
      .raddr_i(rom_addr),
      .rdata_o(instr)
  );

  // ------------------------------------------------------------
  // RAM
  // ------------------------------------------------------------

  antrv_mem #(
      .ADDR_WIDTH(RAM_ADDR_WIDTH),
      .DATA_WIDTH(32),
      .INIT_FILE (RAM_INIT_FILE)
  ) inst_ram (
      .wclk_i (clk_i),
      .rclk_i (clk_i),
      .we_i   (ram_we),
      .wmask_i(ram_wmask),
      .waddr_i(ram_addr),
      .wdata_i(ram_wdata),
      .raddr_i(ram_addr),
      .rdata_o(ram_rdata)
  );

  // ------------------------------------------------------------
  // CPU-to-APB bridge (single bridge)
  // ------------------------------------------------------------

  antrv_apb3_bridge inst_apb_bridge (
      .clk_i  (clk_i),
      .rst_n_i(rst_n_i),

      .req_i  (cpu_req && peripheral_selected),
      .we_i   (cpu_we),
      .addr_i (cpu_byte_addr),
      .wdata_i(ram_wdata),
      .wmask_i(ram_wmask),

      .ready_o(peripheral_ready),
      .rdata_o(peripheral_rdata),
      .error_o(unused_peripheral_error),

      .m_apb(cpu_apb)
  );

  // ------------------------------------------------------------
  // APB decoder / interconnect
  // ------------------------------------------------------------

  antrv_apb3_decoder #(
      .N        (2),
      .BASE_ADDR('{GpioBaseAddr, UartBaseAddr}),
      .SIZE     ('{GpioSize, UartSize})
  ) inst_apb_decoder (
      .m_apb(cpu_apb),
      .s_apb(peripheral_apb)
  );

  // ------------------------------------------------------------
  // GPIO
  // ------------------------------------------------------------

  gpio_top #(
      .GPIO_WIDTH(GPIO_WIDTH)
  ) inst_gpio (
      .clk_i       (clk_i),
      .rst_n_i     (rst_n_i),
      .s_apb       (peripheral_apb[IdGpio]),
      .gpio_pins_io(gpio_pins_io)
  );

  // ------------------------------------------------------------
  // UART
  // ------------------------------------------------------------

  logic unused_rx;
  logic unused_tx;

  uart_top #(
      .BAUD_RATE (BAUD_RATE),
      .CLOCK_FREQ(CLOCK_FREQ)
  ) inst_uart (
      .clk_i  (clk_i),
      .rst_n_i(rst_n_i),
      .s_apb  (peripheral_apb[IdUart]),
      .rx_i   (unused_rx),
      .tx_o   (unused_tx)
  );

endmodule
