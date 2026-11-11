
module antrv_apb3_decoder #(
    parameter int          N            = 2,
    parameter logic [31:0] BASE_ADDR[N] = '{default: 32'b0},
    parameter logic [31:0] SIZE     [N] = '{default: 32'b0}
) (
    // APB master
    apb3_intf.slave m_apb,

    // APB slaves
    apb3_intf.master s_apb[N]
);

  // ------------------------------------------------------------
  // Address decoding
  // ------------------------------------------------------------

  integer selected_slave;

  always_comb begin
    selected_slave = -1;

    for (int i = 0; i < N; i++) begin
      if (
          m_apb.PADDR >= BASE_ADDR[i] &&
          m_apb.PADDR < BASE_ADDR[i] + SIZE[i] &&
          selected_slave == -1
      ) begin
        selected_slave = i;
      end
    end
  end

  // ------------------------------------------------------------
  // Slave response signals
  // ------------------------------------------------------------

  logic [N-1:0] slave_ready;
  logic [N-1:0] slave_error;
  logic [N-1:0][31:0] slave_rdata;

  // ------------------------------------------------------------
  // APB slave connections
  // ------------------------------------------------------------

  for (genvar i = 0; i < N; i++) begin : gen_slaves

    always_comb begin

      // Default signals
      s_apb[i].PSEL    = 1'b0;
      s_apb[i].PENABLE = m_apb.PENABLE;
      s_apb[i].PWRITE  = m_apb.PWRITE;
      s_apb[i].PADDR   = 32'b0;
      s_apb[i].PWDATA  = m_apb.PWDATA;

      // Select peripheral
      if (selected_slave == i) begin
        s_apb[i].PSEL  = m_apb.PSEL;
        s_apb[i].PADDR = m_apb.PADDR - BASE_ADDR[i];
      end

    end

    // Collect slave responses
    assign slave_ready[i] = s_apb[i].PREADY;
    assign slave_rdata[i] = s_apb[i].PRDATA;
    assign slave_error[i] = s_apb[i].PSLVERR;

  end

  // ------------------------------------------------------------
  // APB master response
  // ------------------------------------------------------------

  always_comb begin

    // Default response
    m_apb.PREADY  = 1'b1;
    m_apb.PRDATA  = 32'b0;
    m_apb.PSLVERR = 1'b0;

    // Selected slave response
    if (selected_slave != -1) begin
      m_apb.PREADY  = slave_ready[selected_slave];
      m_apb.PRDATA  = slave_rdata[selected_slave];
      m_apb.PSLVERR = slave_error[selected_slave];
    end  // Unmapped address
    else if (m_apb.PSEL) begin
      m_apb.PREADY  = 1'b1;
      m_apb.PRDATA  = 32'b0;
      m_apb.PSLVERR = 1'b1;
    end

  end

endmodule
