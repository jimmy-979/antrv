
interface apb3_intf #(
    parameter int ADDR_WIDTH = 32,
    parameter int DATA_WIDTH = 32
) (
    input logic PCLK,
    input logic PRESETn
);

  // APB3 signals
  logic                  PSEL;
  logic                  PENABLE;
  logic                  PWRITE;
  logic [ADDR_WIDTH-1:0] PADDR;
  logic [DATA_WIDTH-1:0] PWDATA;
  logic [DATA_WIDTH-1:0] PRDATA;
  logic                  PREADY;
  logic                  PSLVERR;

  // Master drives request signals and receives response signals
  modport master(
      input PCLK,
      input PRESETn,

      output PSEL,
      output PENABLE,
      output PWRITE,
      output PADDR,
      output PWDATA,

      input PRDATA,
      input PREADY,
      input PSLVERR
  );

  // Slave receives request signals and drives response signals
  modport slave(
      input PCLK,
      input PRESETn,

      input PSEL,
      input PENABLE,
      input PWRITE,
      input PADDR,
      input PWDATA,

      output PRDATA,
      output PREADY,
      output PSLVERR
  );

endinterface
