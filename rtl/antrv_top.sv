module antrv_top (
    input logic clk_i
);

  localparam ROM_ADDR_WIDTH = 9;

  logic [ROM_ADDR_WIDTH-1:0] rom_addr;
  logic [              31:0] instr;

  antrv_cpu #(
      .IMEM_ADDR_WIDTH(ROM_ADDR_WIDTH)
  ) inst_cpu (
      .clk_i      (clk_i),
      .imem_addr_o(rom_addr),
      .imem_data_i(instr)
  );

  antrv_mem #(
      .ADDR_WIDTH(ROM_ADDR_WIDTH),
      .DATA_WIDTH(32)
  ) inst_rom (
      .wclk_i (clk_i),
      .rclk_i (clk_i),
      .we_i   (0),
      .waddr_i(0),
      .wdata_i(0),
      .raddr_i(rom_addr),
      .rdata_o(instr)
  );

endmodule
