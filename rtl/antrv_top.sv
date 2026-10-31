module antrv_top #(
    parameter int ROM_ADDR_WIDTH = $clog2('h40000),
    parameter int RAM_ADDR_WIDTH = $clog2('h20000)
) (
    input logic clk_i,
    input logic rst_n_i
);

  logic [ROM_ADDR_WIDTH-1:0] rom_addr;
  logic [              31:0] instr;

  logic                      ram_we;
  logic [               3:0] ram_wmask;
  logic [RAM_ADDR_WIDTH-1:0] ram_addr;
  logic [              31:0] ram_wdata;
  logic [              31:0] ram_rdata;

  antrv_cpu #(
      .IMEM_ADDR_WIDTH(ROM_ADDR_WIDTH),
      .DMEM_ADDR_WIDTH(RAM_ADDR_WIDTH)
  ) inst_cpu (
      .clk_i       (clk_i),
      .rst_n_i     (rst_n_i),
      .imem_addr_o (rom_addr),
      .imem_data_i (instr),
      .dmem_we_o   (ram_we),
      .dmem_wmask_o(ram_wmask),
      .dmem_addr_o (ram_addr),
      .dmem_wdata_o(ram_wdata),
      .dmem_rdata_i(ram_rdata)
  );

  antrv_mem #(
      .ADDR_WIDTH(ROM_ADDR_WIDTH),
      .DATA_WIDTH(32)
  ) inst_rom (
      .wclk_i (clk_i),
      .rclk_i (clk_i),
      .we_i   (0),
      .wmask_i('0),
      .waddr_i(0),
      .wdata_i(0),
      .raddr_i(rom_addr),
      .rdata_o(instr)
  );

  antrv_mem #(
      .ADDR_WIDTH(RAM_ADDR_WIDTH),
      .DATA_WIDTH(32)
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

endmodule
