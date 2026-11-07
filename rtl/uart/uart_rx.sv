module uart_rx #(
    parameter int BAUD_RATE  = 115200,
    parameter int CLOCK_FREQ = 25_000_000
) (
    input  logic       clk_i,
    input  logic       rst_n_i,
    input  logic       rx_serial_i,
    output logic       rx_dv_o,
    output logic [7:0] rx_byte_o
);

  localparam int ClocksPerBit = (CLOCK_FREQ + BAUD_RATE / 2) / BAUD_RATE;
  localparam int CountWidth = $clog2(ClocksPerBit + 1);

  typedef enum logic [1:0] {
    RX_IDLE,
    RX_START,
    RX_DATA,
    RX_STOP
  } rx_state_t;

  // -------------------------- Internal signals --------------------------- //
  logic      [           1:0] rx_sync_reg;
  logic                       rx_sync;
  logic      [CountWidth-1:0] clocks_left;
  logic      [           2:0] bit_idx;
  logic      [           7:0] shift_reg;
  rx_state_t                  state;


  // ------------------------ Input synchronization ------------------------ //
  always_ff @(posedge clk_i or negedge rst_n_i) begin
    if (!rst_n_i) begin
      rx_sync_reg <= 2'b11;
    end else begin
      rx_sync_reg <= {rx_sync_reg[0], rx_serial_i};
    end
  end

  assign rx_sync = rx_sync_reg[1];

  // --------------------------- Receive control --------------------------- //
  always_ff @(posedge clk_i or negedge rst_n_i) begin
    if (!rst_n_i) begin
      state       <= RX_IDLE;
      clocks_left <= {CountWidth{1'b0}};
      bit_idx     <= 3'd0;
      shift_reg   <= 8'h00;
      rx_dv_o     <= 1'b0;
      rx_byte_o   <= 8'h00;
    end else begin
      rx_dv_o <= 1'b0;

      case (state)
        RX_IDLE: begin
          clocks_left <= {CountWidth{1'b0}};
          bit_idx     <= 3'd0;
          if (!rx_sync) begin
            clocks_left <= CountWidth'(ClocksPerBit / 2);
            state       <= RX_START;
          end
        end

        RX_START: begin
          if (clocks_left <= 1) begin
            if (!rx_sync) begin
              clocks_left <= CountWidth'(ClocksPerBit);
              state       <= RX_DATA;
            end else begin
              state <= RX_IDLE;
            end
          end else begin
            clocks_left <= clocks_left - CountWidth'(1);
          end
        end

        RX_DATA: begin
          if (clocks_left <= 1) begin
            shift_reg   <= {rx_sync, shift_reg[7:1]};
            clocks_left <= CountWidth'(ClocksPerBit);

            if (bit_idx == 3'd7) begin
              state <= RX_STOP;
            end else begin
              bit_idx <= bit_idx + 1'b1;
            end
          end else begin
            clocks_left <= clocks_left - CountWidth'(1);
          end
        end

        RX_STOP: begin
          if (clocks_left <= 1) begin
            clocks_left <= {CountWidth{1'b0}};
            state       <= RX_IDLE;
            if (rx_sync) begin
              rx_byte_o <= shift_reg;
              rx_dv_o   <= 1'b1;
            end
          end else begin
            clocks_left <= clocks_left - CountWidth'(1);
          end
        end

        default: begin
          state       <= RX_IDLE;
          clocks_left <= {CountWidth{1'b0}};
        end
      endcase
    end
  end

endmodule
