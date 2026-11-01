`ifndef ANTRV_ROM_INIT_FILE
`define ANTRV_ROM_INIT_FILE ""
`endif
`ifndef ANTRV_RAM_INIT_FILE
`define ANTRV_RAM_INIT_FILE ""
`endif

module antrv_top #(
    parameter int           ROM_ADDR_WIDTH = $clog2(32'h40000),
    parameter int           RAM_ADDR_WIDTH = $clog2(32'h20000),
    parameter int           GPIO_WIDTH     = gpio_reg_file_pkg::GPIO_WIDTH,
    parameter logic  [31:0] GPIO_BASE_ADDR = 32'h80060000,
    parameter string        ROM_INIT_FILE  = `ANTRV_ROM_INIT_FILE,
    parameter string        RAM_INIT_FILE  = `ANTRV_RAM_INIT_FILE
) (
    input logic                  clk_i,
    input logic                  rst_n_i,
    inout wire  [GPIO_WIDTH-1:0] gpio_pins_io
);

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
  logic                      gpio_selected;
  logic                      cpu_using_gpio;
  logic                      gpio_ready;
  logic [              31:0] gpio_rdata;
  logic [              31:0] gpio_read_result;
  logic                      unused_gpio_error;

  assign ram_addr = {2'b00, cpu_byte_addr[RAM_ADDR_WIDTH-1:2]};
  assign gpio_selected = cpu_byte_addr[31:4] == GPIO_BASE_ADDR[31:4];
  assign ram_we = cpu_we && !gpio_selected;
  assign cpu_ready = gpio_selected ? gpio_ready : 1'b1;
  assign cpu_rdata = cpu_using_gpio ? gpio_read_result : ram_rdata;

  always_ff @(posedge clk_i or negedge rst_n_i) begin
    if (!rst_n_i) begin
      cpu_using_gpio   <= 1'b0;
      gpio_read_result <= '0;
    end else begin
      if (cpu_req) begin
        cpu_using_gpio <= gpio_selected;
      end
      if (gpio_ready) begin
        gpio_read_result <= gpio_rdata;
      end
    end
  end

  antrv_cpu #(
      .IMEM_ADDR_WIDTH(ROM_ADDR_WIDTH)
  ) inst_cpu (
      .clk_i       (clk_i),
      .rst_n_i     (rst_n_i),
      .imem_addr_o (rom_addr),
      .imem_data_i (instr),
      .dmem_we_o   (cpu_we),
      .dmem_wmask_o(ram_wmask),
      .dmem_addr_o (cpu_byte_addr),
      .dmem_wdata_o(ram_wdata),
      .dmem_rdata_i(cpu_rdata),
      .dmem_req_o  (cpu_req),
      .dmem_ready_i(cpu_ready)
  );

  antrv_mem #(
      .ADDR_WIDTH(ROM_ADDR_WIDTH),
      .DATA_WIDTH(32),
      .INIT_FILE (ROM_INIT_FILE)
  ) inst_rom (
      .wclk_i (clk_i),
      .rclk_i (clk_i),
      .we_i   (0),
      .wmask_i(0),
      .waddr_i(0),
      .wdata_i(0),
      .raddr_i(rom_addr),
      .rdata_o(instr)
  );

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

  apb3_intf gpio_apb (
      .PCLK   (clk_i),
      .PRESETn(rst_n_i)
  );

  antrv_apb3_bridge inst_apb_bridge (
      .clk_i  (clk_i),
      .rst_n_i(rst_n_i),
      .req_i  (cpu_req && gpio_selected),
      .we_i   (cpu_we),
      .addr_i (cpu_byte_addr - GPIO_BASE_ADDR),
      .wdata_i(ram_wdata),
      .wmask_i(ram_wmask),
      .ready_o(gpio_ready),
      .rdata_o(gpio_rdata),
      .error_o(unused_gpio_error),
      .m_apb  (gpio_apb)
  );

  gpio_top #(
      .GPIO_WIDTH(GPIO_WIDTH)
  ) inst_gpio (
      .clk_i       (clk_i),
      .rst_n_i     (rst_n_i),
      .s_apb       (gpio_apb),
      .gpio_pins_io(gpio_pins_io)
  );

endmodule
