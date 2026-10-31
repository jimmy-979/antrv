module antrv_apb3_bridge (
    input  logic        clk_i,
    input  logic        rst_n_i,
    input  logic        req_i,
    input  logic        we_i,
    input  logic [31:0] addr_i,
    input  logic [31:0] wdata_i,
    input  logic [3:0]  wmask_i,
    output logic        ready_o,
    output logic [31:0] rdata_o,
    output logic        error_o,
    apb3_intf.master    m_apb
);
  typedef enum logic [1:0] {IDLE, SETUP, ACCESS, REJECT} state_t;
  state_t state;

  assign m_apb.PSEL = state == SETUP || state == ACCESS;
  assign m_apb.PENABLE = state == ACCESS;
  assign ready_o = state == REJECT || (state == ACCESS && m_apb.PREADY);
  assign error_o = state == REJECT ||
                   (state == ACCESS && m_apb.PREADY && m_apb.PSLVERR);
  assign rdata_o = state == REJECT ? 32'b0 : m_apb.PRDATA;

  always_ff @(posedge clk_i or negedge rst_n_i) begin
    if (!rst_n_i) begin
      state <= IDLE;
      m_apb.PADDR <= '0;
      m_apb.PWDATA <= '0;
      m_apb.PWRITE <= 1'b0;
    end else begin
      case (state)
        IDLE: begin
          if (req_i) begin
            m_apb.PADDR <= {addr_i[31:2], 2'b00};
            m_apb.PWDATA <= wdata_i;
            m_apb.PWRITE <= we_i;
            state <= we_i && (wmask_i != 4'b1111 || addr_i[1:0] != 2'b00)
                ? REJECT : SETUP;
          end
        end
        SETUP: state <= ACCESS;
        ACCESS: if (m_apb.PREADY) state <= IDLE;
        REJECT: state <= IDLE;
        default: state <= IDLE;
      endcase
    end
  end
endmodule
