module uart_tx #(
    parameter int BAUD_RATE  = 115200,
    parameter int CLOCK_FREQ = 25_000_000
) (
    input  logic       clk_i,
    input  logic       rst_n_i,
    input  logic       tx_valid_i,
    input  logic [7:0] tx_byte_i,
    output logic       tx_ready_o,
    output logic       tx_active_o,
    output logic       tx_done_o,
    output logic       tx_serial_o
);

  localparam int ClocksPerBit = (CLOCK_FREQ + BAUD_RATE / 2) / BAUD_RATE;
  localparam int CountWidth = $clog2(ClocksPerBit + 1);

  typedef enum logic [1:0] {
    TX_IDLE,
    TX_START,
    TX_DATA,
    TX_STOP
  } tx_state_t;

  // -------------------------- Internal signals --------------------------- //
  logic      [CountWidth-1:0] clocks_left;
  logic      [           2:0] bit_idx;
  logic      [           7:0] shift_reg;
  tx_state_t                  state;

  assign tx_ready_o  = (state == TX_IDLE);
  assign tx_active_o = (state != TX_IDLE);

  // -------------------------- Transmit control --------------------------- //
  always_ff @(posedge clk_i or negedge rst_n_i) begin
    if (!rst_n_i) begin
      state       <= TX_IDLE;
      clocks_left <= {CountWidth{1'b0}};
      bit_idx     <= 3'd0;
      shift_reg   <= 8'h00;
      tx_serial_o <= 1'b1;
      tx_done_o   <= 1'b0;
    end else begin
      tx_done_o <= 1'b0;

      case (state)
        TX_IDLE: begin
          tx_serial_o <= 1'b1;
          if (tx_valid_i) begin
            clocks_left <= CountWidth'(ClocksPerBit);
            shift_reg   <= tx_byte_i;
            bit_idx     <= 3'd0;
            tx_serial_o <= 1'b0;
            state       <= TX_START;
          end
        end

        TX_START: begin
          if (clocks_left <= 1) begin
            clocks_left <= CountWidth'(ClocksPerBit);
            tx_serial_o <= shift_reg[0];
            shift_reg   <= {1'b0, shift_reg[7:1]};
            state       <= TX_DATA;
          end else begin
            clocks_left <= clocks_left - CountWidth'(1);
          end
        end

        TX_DATA: begin
          if (clocks_left <= 1) begin
            clocks_left <= CountWidth'(ClocksPerBit);
            if (bit_idx == 3'd7) begin
              tx_serial_o <= 1'b1;
              state       <= TX_STOP;
            end else begin
              tx_serial_o <= shift_reg[0];
              shift_reg   <= {1'b0, shift_reg[7:1]};
              bit_idx     <= bit_idx + 1'b1;
            end
          end else begin
            clocks_left <= clocks_left - CountWidth'(1);
          end
        end

        TX_STOP: begin
          if (clocks_left <= 1) begin
            clocks_left <= {CountWidth{1'b0}};
            state       <= TX_IDLE;
            tx_done_o   <= 1'b1;
          end else begin
            clocks_left <= clocks_left - CountWidth'(1);
          end
        end

        default: begin
          state       <= TX_IDLE;
          clocks_left <= {CountWidth{1'b0}};
          tx_serial_o <= 1'b1;
        end
      endcase
    end
  end

endmodule
