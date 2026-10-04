module antrv_cpu #(
    parameter IMEM_ADDR_WIDTH = 9
) (
    input  logic                       clk_i,
    output logic [IMEM_ADDR_WIDTH-1:0] imem_addr_o,
    input  logic [               31:0] imem_data_i
);

  localparam XLEN = 32;

  logic [XLEN-1:0] pc = 0;

  // PC generation
  always_ff @(posedge clk_i) begin
    pc <= pc + 4;
  end

  assign imem_addr_o = pc;

  // Instruction decoding

  // ALU
  antrv_alu #(
      .DATA_WIDTH(XLEN)
  ) inst_alu (
      .clk_i      (clk_i),
      .ina_i      (),
      .inb_i      (),
      .in_ready_i (),
      .operation_i(),
      .res_o      (),
      .res_valid_o()
  );

  // Register file
  antrv_regfile #(
      .ADDR_WIDTH(5),
      .DATA_WIDTH(XLEN)
  ) inst_regfile (
      .wclk_i (clk_i),
      .rclk_i (clk_i),
      .we_i   (),
      .waddr_i(),
      .wdata_i(),
      .raddr_i(),
      .rdata_o()
  );

endmodule
