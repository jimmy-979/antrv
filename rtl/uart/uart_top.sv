module uart_top #(
    parameter int BAUD_RATE  = 115200,
    parameter int CLOCK_FREQ = 25_000_000
) (
    input  logic           clk_i,
    input  logic           rst_n_i,
           apb3_intf.slave s_apb,
    input  logic           rx_i,
    output logic           tx_o
);

  uart_reg_file_pkg::uart_reg_file__in_t  hwif_in;
  uart_reg_file_pkg::uart_reg_file__out_t hwif_out;

  logic                                   unused_tx_ready;
  logic                                   unused_tx_done;
  logic                                   tx_valid_q;

  always_ff @(posedge clk_i or negedge rst_n_i) begin
    if (!rst_n_i) begin
      tx_valid_q <= 1'b0;
    end else begin
      tx_valid_q <= hwif_out.tx_data.data.swmod;
    end
  end

  uart_rx #(
      .BAUD_RATE (BAUD_RATE),
      .CLOCK_FREQ(CLOCK_FREQ)
  ) inst_rx (
      .clk_i      (clk_i),
      .rst_n_i    (rst_n_i),
      .rx_serial_i(rx_i),
      .rx_dv_o    (hwif_in.status.rx_valid.hwset),
      .rx_byte_o  (hwif_in.rx_data.data.next)
  );

  uart_tx #(
      .BAUD_RATE (BAUD_RATE),
      .CLOCK_FREQ(CLOCK_FREQ)
  ) inst_tx (
      .clk_i      (clk_i),
      .rst_n_i    (rst_n_i),
      .tx_valid_i (tx_valid_q),
      .tx_byte_i  (hwif_out.tx_data.data.value),
      .tx_ready_o (unused_tx_ready),
      .tx_active_o(hwif_in.status.tx_busy.next),
      .tx_done_o  (unused_tx_done),
      .tx_serial_o(tx_o)
  );

  uart_reg_file inst_reg_file (
      .clk     (clk_i),
      .arst_n  (rst_n_i),
      .s_apb   (s_apb),
      .hwif_in (hwif_in),
      .hwif_out(hwif_out)
  );

endmodule
