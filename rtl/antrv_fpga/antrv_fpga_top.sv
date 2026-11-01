module antrv_fpga_top (
    input  logic i_Clk,
    inout  logic o_LED_1,
    inout  logic o_LED_2,
    inout  logic o_LED_3,
    inout  logic o_LED_4,
    inout  logic i_Switch_1,
    inout  logic i_Switch_2,
    inout  logic i_Switch_3,
    inout  logic i_Switch_4,
    output logic o_Segment1_A,
    output logic o_Segment1_B,
    output logic o_Segment1_C,
    output logic o_Segment1_D,
    output logic o_Segment1_E,
    output logic o_Segment1_F,
    output logic o_Segment1_G,
    output logic o_Segment2_A,
    output logic o_Segment2_B,
    output logic o_Segment2_C,
    output logic o_Segment2_D,
    output logic o_Segment2_E,
    output logic o_Segment2_F,
    output logic o_Segment2_G,
    input  logic i_UART_RX,
    output logic o_UART_TX,
    output logic o_VGA_HSync,
    output logic o_VGA_VSync,
    output logic o_VGA_Red_0,
    output logic o_VGA_Red_1,
    output logic o_VGA_Red_2,
    output logic o_VGA_Grn_0,
    output logic o_VGA_Grn_1,
    output logic o_VGA_Grn_2,
    output logic o_VGA_Blu_0,
    output logic o_VGA_Blu_1,
    output logic o_VGA_Blu_2,
    inout  logic io_PMOD_1,
    inout  logic io_PMOD_2,
    inout  logic io_PMOD_3,
    inout  logic io_PMOD_4,
    inout  logic io_PMOD_7,
    inout  logic io_PMOD_8,
    inout  logic io_PMOD_9,
    inout  logic io_PMOD_10
);

  antrv_top #(
      .ROM_ADDR_WIDTH($clog2(256)),
      .RAM_ADDR_WIDTH($clog2(256)),
      .GPIO_WIDTH    (8)
  ) inst_antrv_top (
      .clk_i(i_Clk),
      .rst_n_i(1'b1),
      .gpio_pins_io({
        o_LED_4, o_LED_3, o_LED_2, o_LED_1, i_Switch_4, i_Switch_3, i_Switch_2, i_Switch_1
      })
  );

endmodule
