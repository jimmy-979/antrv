module antrv_alu #(
    parameter DATA_WIDTH = 32
) (
    input  logic                                clk_i,
    input  logic               [DATA_WIDTH-1:0] ina_i,
    input  logic               [DATA_WIDTH-1:0] inb_i,
    input  logic                                in_ready_i,
    input  antrv_pkg::t_alu_op                  operation_i,
    output logic               [DATA_WIDTH-1:0] res_o,
    output logic                                res_valid_o
);

  logic [        DATA_WIDTH-1:0] inb_xored;
  logic [$clog2(DATA_WIDTH)-1:0] idx = 0;
  logic                          sum;
  logic                          carry_in;
  logic                          carry_out;
  logic                          is_sub;

  assign is_sub = operation_i == antrv_pkg::ALU_SUB;

  assign inb_xored = inb_i ^ {DATA_WIDTH{is_sub}};
  assign {carry_out, sum} = ina_i[idx] + inb_xored[idx] + carry_in;

  always_ff @(posedge clk_i) begin
    if (in_ready_i) begin
      idx         <= idx + 1;
      res_o       <= {sum, res_o[DATA_WIDTH-1:1]};
      carry_in    <= carry_out;
      res_valid_o <= &idx;
    end else begin
      idx         <= 0;
      carry_in    <= is_sub;
      res_valid_o <= 0;
    end
  end
endmodule
