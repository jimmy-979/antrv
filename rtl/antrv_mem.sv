module antrv_mem #(
    parameter int ADDR_WIDTH = 9,
    parameter int DATA_WIDTH = 32
) (
    input  logic                    wclk_i,
    input  logic                    rclk_i,
    input  logic                    we_i,
    input  logic [DATA_WIDTH/8-1:0] wmask_i,
    input  logic [  ADDR_WIDTH-1:0] waddr_i,
    input  logic [  DATA_WIDTH-1:0] wdata_i,
    input  logic [  ADDR_WIDTH-1:0] raddr_i,
    output logic [  DATA_WIDTH-1:0] rdata_o
);

  logic [DATA_WIDTH-1:0] mem[1<<ADDR_WIDTH];

  always_ff @(posedge wclk_i) begin
    if (we_i) begin
      for (int byte_idx = 0; byte_idx < DATA_WIDTH / 8; byte_idx++) begin
        if (wmask_i[byte_idx]) begin
          mem[waddr_i][byte_idx*8+:8] <= wdata_i[byte_idx*8+:8];
        end
      end
    end
  end

  always_ff @(posedge rclk_i) begin
    rdata_o <= mem[raddr_i];
  end

endmodule
