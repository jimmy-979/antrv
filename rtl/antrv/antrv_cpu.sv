module antrv_cpu #(
    parameter int IMEM_ADDR_WIDTH = 9,
    parameter int XLEN            = 32
) (
    input  logic                       clk_i,
    input  logic                       rst_n_i,
    output logic [IMEM_ADDR_WIDTH-1:0] imem_addr_o,
    input  logic [               31:0] imem_data_i,
    output logic                       dmem_we_o,
    output logic [                3:0] dmem_wmask_o,
    output logic [               31:0] dmem_addr_o,
    output logic [               31:0] dmem_wdata_o,
    input  logic [               31:0] dmem_rdata_i,
    output logic                       dmem_req_o,
    input  logic                       dmem_ready_i
);

  logic [XLEN-1:0] pc;
  logic [XLEN-1:0] next_pc;
  // Instruction decoding
  logic [     4:0] rs1;
  logic [     4:0] rs2;
  logic [     4:0] rd;
  logic [     2:0] funct3;
  logic            funct7;
  typedef enum logic [4:0] {
    LOAD     = 5'b00000,
    MISC_MEM = 5'b00011,
    OP_IMM   = 5'b00100,
    AUIPC    = 5'b00101,
    STORE    = 5'b01000,
    OP       = 5'b01100,
    LUI      = 5'b01101,
    BRANCH   = 5'b11000,
    JALR     = 5'b11001,
    JAL      = 5'b11011,
    SYSTEM   = 5'b11100
  } opcode_t;
  opcode_t            opcode;
  logic    [    31:0] immI;
  logic    [    31:0] immS;
  logic    [    31:0] immB;
  logic    [    31:0] immU;
  logic    [    31:0] immJ;
  // ALU
  logic    [XLEN-1:0] alu_ina;
  logic    [XLEN-1:0] alu_inb;
  logic    [XLEN-1:0] alu_result;
  logic               alu_zero;
  logic               latched_alu_zero;
  logic               alu_carry_out;
  logic               latched_alu_carry_out;
  logic               signed_less;
  logic               latched_signed_less;
  // Register file
  logic    [XLEN-1:0] rf_wdata;
  logic    [XLEN-1:0] rf_rdata;
  logic    [XLEN-1:0] latched_rf_rdata;
  logic    [     4:0] rf_raddr;
  logic    [     1:0] load_offset;
  logic    [    15:0] load_half;
  logic    [     7:0] load_byte;
  logic               load_sign;
  logic    [    31:0] load_data;
  // Control
  typedef enum logic [1:0] {
    INSTR,
    PC,
    ALU,
    LATCH_RF
  } state_t;
  logic               [1:0] instr_wait;
  logic                     latch_rf_wait;
  logic                     dmem_rdata_valid;
  state_t                   state;
  logic                     pc_update;
  logic                     rf_sel_rs2;
  logic                     alu_input_ready;
  antrv_pkg::alu_op_t       alu_operation;
  logic                     alu_result_valid;
  logic                     rf_we;
  logic                     memory_pending;
  logic [31:0]              memory_addr;

  // ---------------------------- PC generation ---------------------------- //
  always_ff @(posedge clk_i or negedge rst_n_i) begin
    if (!rst_n_i) begin
      pc <= 'h80000000;
    end else begin
      if (pc_update) begin
        pc <= next_pc;
      end
    end
  end

  always_ff @(posedge clk_i or negedge rst_n_i) begin
    if (!rst_n_i) begin
      next_pc <= 0;
    end else begin
      if (state == PC && alu_result_valid) begin
        next_pc <= opcode == JALR ? {alu_result[XLEN-1:1], 1'b0} : alu_result;
      end
    end
  end

  // ---------------------- Instruction / Data buses ----------------------- //
  assign imem_addr_o = {2'b00, pc[IMEM_ADDR_WIDTH-1:2]};

  assign dmem_req_o = state == ALU && (opcode == LOAD || opcode == STORE) &&
                      (alu_result_valid || memory_pending) && !dmem_rdata_valid;
  assign dmem_we_o = opcode == STORE && dmem_req_o;
  assign dmem_addr_o = memory_pending ? memory_addr : alu_result;

  always_ff @(posedge clk_i or negedge rst_n_i) begin
    if (!rst_n_i) begin
      memory_pending <= 1'b0;
      memory_addr <= '0;
    end else if (dmem_req_o) begin
      memory_pending <= !dmem_ready_i;
      if (!memory_pending) memory_addr <= alu_result;
    end
  end

  always_comb begin
    case (funct3)
      3'b000: begin
        dmem_wmask_o = 4'b0001 << dmem_addr_o[1:0];
        dmem_wdata_o = {4{latched_rf_rdata[7:0]}};
      end
      3'b001: begin
        dmem_wmask_o = dmem_addr_o[1] ? 4'b1100 : 4'b0011;
        dmem_wdata_o = {2{latched_rf_rdata[15:0]}};
      end
      default: begin
        dmem_wmask_o = 4'b1111;
        dmem_wdata_o = latched_rf_rdata;
      end
    endcase
  end

  // ------------------------ Instruction decoding ------------------------- //
  // Register fields
  assign rs1 = imem_data_i[19:15];
  assign rs2 = imem_data_i[24:20];
  assign rd = imem_data_i[11:7];
  // Function fields
  assign funct3 = imem_data_i[14:12];
  assign funct7 = imem_data_i[30];
  // Opcode
  assign opcode = opcode_t'(imem_data_i[1:0] == 2'b11 ? imem_data_i[6:2] : 5'b11111);
  // Immediate fields
  assign immI = {{20{imem_data_i[31]}}, imem_data_i[31:20]};
  assign immS = {{20{imem_data_i[31]}}, imem_data_i[31:25], imem_data_i[11:7]};
  assign immB = {
    {19{imem_data_i[31]}},
    imem_data_i[31],
    imem_data_i[7],
    imem_data_i[30:25],
    imem_data_i[11:8],
    1'b0
  };
  assign immU = {imem_data_i[31:12], 12'b0};
  assign immJ = {
    {11{imem_data_i[31]}},
    imem_data_i[31],
    imem_data_i[19:12],
    imem_data_i[20],
    imem_data_i[30:21],
    1'b0
  };

  // --------------------------------- ALU --------------------------------- //
  always_comb begin
    // ALU 1st input
    if (state == PC) begin
      case (opcode)
        JALR:    alu_ina = rf_rdata;
        default: alu_ina = pc;
      endcase
    end else begin
      case (opcode)
        LOAD:    alu_ina = rf_rdata;  // LOAD
        OP_IMM:  alu_ina = rf_rdata;  // OP-IMM
        AUIPC:   alu_ina = pc;  // AUIPC
        STORE:   alu_ina = rf_rdata;  // STORE
        OP:      alu_ina = rf_rdata;  // OP
        LUI:     alu_ina = 0;  // LUI
        BRANCH:  alu_ina = rf_rdata;  // BRANCH
        JALR:    alu_ina = pc;  // JALR
        JAL:     alu_ina = pc;  // JAL
        SYSTEM:  alu_ina = 0;  // SYSTEM
        default: alu_ina = 0;
      endcase
    end

    // ALU 2nd input
    if (state == PC) begin
      case (opcode)
        JALR: alu_inb = immI;
        JAL: alu_inb = immJ;
        BRANCH: begin
          case (funct3)
            3'b000:  alu_inb = latched_alu_zero ? immB : 4;  // BEQ
            3'b001:  alu_inb = !latched_alu_zero ? immB : 4;  // BNE
            3'b100:  alu_inb = latched_signed_less ? immB : 4;  // BLT
            3'b101:  alu_inb = !latched_signed_less ? immB : 4;  // BGE
            3'b110:  alu_inb = !latched_alu_carry_out ? immB : 4;  // BLTU
            3'b111:  alu_inb = latched_alu_carry_out ? immB : 4;  // BGEU
            default: alu_inb = immB;
          endcase
        end
        default: alu_inb = 4;
      endcase
    end else begin
      case (opcode)
        LOAD:    alu_inb = immI;  // LOAD
        OP_IMM:  alu_inb = immI;  // OP-IMM
        AUIPC:   alu_inb = immU;  // AUIPC
        STORE:   alu_inb = immS;  // STORE
        OP:      alu_inb = latched_rf_rdata;  // OP
        LUI:     alu_inb = immU;  // LUI
        BRANCH:  alu_inb = latched_rf_rdata;  // BRANCH
        JALR:    alu_inb = 4;  // JALR
        JAL:     alu_inb = 4;  // JAL
        SYSTEM:  alu_inb = 0;  // SYSTEM
        default: alu_inb = 0;
      endcase
    end
  end

  assign signed_less = (alu_ina[XLEN-1] != alu_inb[XLEN-1]) ? alu_ina[XLEN-1] : alu_result[XLEN-1];

  always_ff @(posedge clk_i or negedge rst_n_i) begin
    if (!rst_n_i) begin
      latched_rf_rdata      <= 0;
      latched_alu_zero      <= 0;
      latched_alu_carry_out <= 0;
      latched_signed_less   <= 0;
      load_offset           <= 0;
    end else begin
      if (state == LATCH_RF) begin
        latched_rf_rdata <= rf_rdata;
      end
      if (opcode == LOAD && state == ALU && alu_result_valid) begin
        load_offset <= alu_result[1:0];
      end
      if (state == ALU && alu_result_valid) begin
        latched_signed_less <= signed_less;
      end
      if (alu_result_valid) begin
        latched_alu_zero      <= alu_zero;
        latched_alu_carry_out <= alu_carry_out;
      end
    end
  end

  antrv_alu #(
      .DATA_WIDTH(XLEN)
  ) inst_alu (
      .clk_i      (clk_i),
      .rst_n_i    (rst_n_i),
      .ina_i      (alu_ina),
      .inb_i      (alu_inb),
      .in_ready_i (alu_input_ready),
      .operation_i(alu_operation),
      .res_o      (alu_result),
      .res_valid_o(alu_result_valid),
      .zero_o     (alu_zero),
      .carry_out_o(alu_carry_out)
  );

  // ---------------------------- Register file ---------------------------- //
  assign rf_we = opcode == LOAD ? dmem_rdata_valid : opcode != BRANCH &&
                                                     opcode != STORE  &&
                                                     opcode != MISC_MEM &&
                                                     alu_result_valid &&
                                                     state == ALU;
  assign rf_raddr = rf_sel_rs2 ? rs2 : rs1;
  assign load_half = load_offset[1] ? dmem_rdata_i[31:16] : dmem_rdata_i[15:0];
  assign load_byte = load_offset[0] ? load_half[15:8] : load_half[7:0];
  assign load_sign = !funct3[2] && (funct3[0] ? load_half[15] : load_byte[7]);

  always_comb begin
    case (funct3[1:0])
      2'b00:   load_data = {{24{load_sign}}, load_byte};
      2'b01:   load_data = {{16{load_sign}}, load_half};
      default: load_data = dmem_rdata_i;
    endcase
  end

  always_comb begin
    rf_wdata = opcode == LOAD ? load_data : alu_result;
    if (opcode == OP || opcode == OP_IMM) begin
      case (funct3)
        3'b010: begin
          rf_wdata = '0;
          rf_wdata[0] = signed_less;
        end
        3'b011: begin
          rf_wdata = '0;
          rf_wdata[0] = !alu_carry_out;
        end
        default: ;
      endcase
    end
  end

  antrv_regfile #(
      .ADDR_WIDTH(5),
      .DATA_WIDTH(XLEN)
  ) inst_regfile (
      .wclk_i (clk_i),
      .rclk_i (clk_i),
      .we_i   (rf_we),
      .waddr_i(rd),
      .wdata_i(rf_wdata),
      .raddr_i(rf_raddr),
      .rdata_o(rf_rdata)
  );

  // ------------------------------- Control ------------------------------- //
  always_comb begin
    if (state == PC) begin
      alu_operation = antrv_pkg::ALU_ADD;
    end else begin
      case (opcode)
        LOAD:    alu_operation = antrv_pkg::ALU_ADD;  // LOAD
        OP_IMM: begin  // OP-IMM
          case (funct3)
            3'b000:  alu_operation = antrv_pkg::ALU_ADD;  // ADDI
            3'b010:  alu_operation = antrv_pkg::ALU_SUB;  // SLTI
            3'b011:  alu_operation = antrv_pkg::ALU_SUB;  // SLTIU
            3'b100:  alu_operation = antrv_pkg::ALU_XOR;  // XORI
            3'b110:  alu_operation = antrv_pkg::ALU_OR;  // ORI
            3'b111:  alu_operation = antrv_pkg::ALU_AND;  // ANDI
            3'b001:  alu_operation = antrv_pkg::ALU_SLL;  // SLLI
            3'b101: begin
              alu_operation = funct7 ? antrv_pkg::ALU_SRA :  // SRA
              antrv_pkg::ALU_SRL;  // SRLI
            end
            default: alu_operation = antrv_pkg::ALU_ADD;
          endcase
        end
        AUIPC:   alu_operation = antrv_pkg::ALU_ADD;  // AUIPC
        STORE:   alu_operation = antrv_pkg::ALU_ADD;  // STORE
        OP: begin  // OP
          case (funct3)
            3'b000: begin
              alu_operation = funct7 ? antrv_pkg::ALU_SUB :  // SUB
              antrv_pkg::ALU_ADD;  // ADD
            end
            3'b001:  alu_operation = antrv_pkg::ALU_SLL;  // SLL
            3'b010:  alu_operation = antrv_pkg::ALU_SUB;  // SLT
            3'b011:  alu_operation = antrv_pkg::ALU_SUB;  // SLTU
            3'b100:  alu_operation = antrv_pkg::ALU_XOR;  // XOR
            3'b101: begin
              alu_operation = funct7 ? antrv_pkg::ALU_SRA :  // SRA
              antrv_pkg::ALU_SRL;  // SRL
            end
            3'b110:  alu_operation = antrv_pkg::ALU_OR;  // OR
            3'b111:  alu_operation = antrv_pkg::ALU_AND;  // AND
            default: alu_operation = antrv_pkg::ALU_AND;
          endcase
        end
        LUI:     alu_operation = antrv_pkg::ALU_ADD;  // LUI
        BRANCH:  alu_operation = antrv_pkg::ALU_SUB;  // BRANCH
        JALR:    alu_operation = antrv_pkg::ALU_ADD;  // JALR
        JAL:     alu_operation = antrv_pkg::ALU_ADD;  // JAL
        SYSTEM:  alu_operation = antrv_pkg::ALU_ADD;  // SYSTEM
        default: alu_operation = antrv_pkg::ALU_ADD;
      endcase
    end
  end

  // In case of JALR we need to save return address and calculate the
  // address to jump to. We don't want to write to the register that
  // will be used to calculate the jump address. So firstly next PC
  // needs to be calculated, then update registers and finally fetch new
  // instruction. But in case of BRANCH instructions firstly the ALU
  // calculation should be performed and after that PC calculation
  always_ff @(posedge clk_i or negedge rst_n_i) begin
    if (!rst_n_i) begin
      state            <= INSTR;
      pc_update        <= 0;
      alu_input_ready  <= 0;
      rf_sel_rs2       <= 0;
      dmem_rdata_valid <= 0;
      instr_wait       <= 0;
      latch_rf_wait    <= 0;
    end else begin
      // Default control outputs
      state            <= INSTR;
      pc_update        <= 0;
      alu_input_ready  <= 0;
      rf_sel_rs2       <= 0;
      dmem_rdata_valid <= 0;
      instr_wait       <= 0;
      latch_rf_wait    <= 0;

      case (state)
        // INSTR: Allow the instruction to be decoded.
        INSTR: begin
          if (&instr_wait) begin
            instr_wait <= 2'b00;
            state      <= opcode == BRANCH ? LATCH_RF : PC;
            rf_sel_rs2 <= opcode == BRANCH;
          end else begin
            instr_wait <= {instr_wait[0], 1'b1};
            state      <= INSTR;
          end
        end

        // PC: Calculate PC + 4 (or the relevant jump address).
        PC: begin
          if (alu_result_valid) begin
            state <= (opcode == OP || opcode == STORE) ? LATCH_RF :
                                    (opcode == BRANCH) ? INSTR : ALU;
            rf_sel_rs2 <= (opcode == OP || opcode == STORE);
            alu_input_ready <= 1'b0;
            pc_update <= opcode == BRANCH;
          end else begin
            state           <= PC;
            alu_input_ready <= 1'b1;
          end
        end

        // LATCH_RF: Allow the second register operand to be captured.
        LATCH_RF: begin
          if (!latch_rf_wait) begin
            latch_rf_wait <= 1'b1;
            state         <= LATCH_RF;
          end else begin
            latch_rf_wait <= 1'b0;
            state         <= ALU;
          end
        end

        // ALU: Execute the instruction and complete memory operations.
        ALU: begin
          if (dmem_rdata_valid) begin
            state           <= opcode == BRANCH ? PC : INSTR;
            pc_update       <= opcode != BRANCH;
            alu_input_ready <= 1'b0;
          end else begin
            state           <= ALU;
            alu_input_ready <= 1'b1;
          end

          if (memory_pending) begin
            alu_input_ready <= 1'b0;
          end

          if (dmem_req_o && dmem_ready_i) begin
            dmem_rdata_valid <= 1'b1;
            alu_input_ready <= 1'b0;
          end else if (alu_result_valid) begin
            dmem_rdata_valid <= opcode != LOAD && opcode != STORE;
            // Prevent zero-distance shifts from completing again after reset.
            alu_input_ready  <= 1'b0;
          end
        end

        default: ;
      endcase
    end
  end

endmodule
