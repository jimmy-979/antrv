module antrv_alu #(
    parameter int DATA_WIDTH = 32
) (
    input logic                                clk_i,
    input logic                                rst_n_i,
    input logic               [DATA_WIDTH-1:0] ina_i,
    input logic               [DATA_WIDTH-1:0] inb_i,
    input logic                                in_ready_i,
    input antrv_pkg::alu_op_t                  operation_i,

    output logic [DATA_WIDTH-1:0] res_o,
    output logic                  res_valid_o,
    output logic                  zero_o,
    output logic                  carry_out_o
);

  localparam int IdxWidth = $clog2(DATA_WIDTH);

  // -------------------------- Internal signals --------------------------- //
  // Iterative state
  logic [  IdxWidth-1:0] bit_idx;
  logic [DATA_WIDTH-1:0] result;
  logic                  carry_in;
  logic                  result_valid;

  // Operation decoding
  logic                  is_sub;
  logic                  is_shift;

  // Arithmetic datapath
  logic                  a_bit;
  logic                  b_bit;
  logic                  add_b_bit;
  logic                  sum;
  logic                  carry_out;
  logic [           1:0] bit_sum;

  // Result datapath
  logic                  serial_bit;
  logic [DATA_WIDTH-1:0] next_result;

  // ------------------------- Operation decoding -------------------------- //
  assign is_sub = (operation_i == antrv_pkg::ALU_SUB);

  assign is_shift =
      (operation_i == antrv_pkg::ALU_SLL) ||
      (operation_i == antrv_pkg::ALU_SRL) ||
      (operation_i == antrv_pkg::ALU_SRA);

  // --------------------- One-bit arithmetic datapath --------------------- //
  assign a_bit = ina_i[bit_idx];
  assign b_bit = inb_i[bit_idx];
  assign add_b_bit = b_bit ^ is_sub;

  assign bit_sum = {1'b0, a_bit} + {1'b0, add_b_bit} + {1'b0, carry_in};

  assign {carry_out, sum} = bit_sum;

  // --------------------------- Result datapath --------------------------- //
  always_comb begin
    // Default: arithmetic operations.
    serial_bit = sum;

    case (operation_i)
      antrv_pkg::ALU_SRA: serial_bit = result[DATA_WIDTH-1];
      antrv_pkg::ALU_SRL: serial_bit = 1'b0;

      antrv_pkg::ALU_AND: serial_bit = a_bit & b_bit;
      antrv_pkg::ALU_OR:  serial_bit = a_bit | b_bit;
      antrv_pkg::ALU_XOR: serial_bit = a_bit ^ b_bit;

      default: ;
    endcase

    // Left shifts use the opposite direction.
    if (operation_i == antrv_pkg::ALU_SLL) next_result = {result[DATA_WIDTH-2:0], 1'b0};
    else next_result = {serial_bit, result[DATA_WIDTH-1:1]};
  end

  // ------------------------ Completion detection ------------------------- //
  always_comb begin
    if (is_shift) res_valid_o = in_ready_i && (bit_idx == inb_i[IdxWidth-1:0]);
    else res_valid_o = result_valid;
  end

  assign res_o  = result;

  assign zero_o = ~|result;

  always_ff @(posedge clk_i or negedge rst_n_i) begin
    if (!rst_n_i) begin
      carry_out_o <= 1'b0;
    end else begin
      carry_out_o <= carry_out;
    end
  end

  // ------------------------- Sequential control -------------------------- //
  always_ff @(posedge clk_i or negedge rst_n_i) begin
    if (!rst_n_i) begin
      bit_idx      <= {IdxWidth{1'b0}};
      result       <= {DATA_WIDTH{1'b0}};
      carry_in     <= 1'b0;
      result_valid <= 1'b0;
    end else begin
      if (res_valid_o) begin
        // Finish the operation and clear the datapath.
        bit_idx      <= {IdxWidth{1'b0}};
        result       <= {DATA_WIDTH{1'b0}};
        carry_in     <= 1'b0;
        result_valid <= 1'b0;

      end else if (!in_ready_i) begin
        // Initialize the datapath before iteration.
        bit_idx      <= {IdxWidth{1'b0}};
        result       <= ina_i;
        carry_in     <= is_sub;
        result_valid <= 1'b0;

      end else begin
        // Process one bit per cycle.
        bit_idx      <= bit_idx + {{(IdxWidth - 1) {1'b0}}, 1'b1};
        result       <= next_result;
        carry_in     <= carry_out;
        result_valid <= &bit_idx;
      end
    end
  end

endmodule
