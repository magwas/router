//-----------------------------------------------------
// this wants to be the same as the Counter example of galasm
// 1 bit counter vith a Clock, Set, and Clear input
// Clock D0    NC    NC    NC    Set   Clear NC    NC   NC NC      GND
// /OE   NC    NC    NC    NC    NC    NC    NC    Q0   NC NC      VCC
//
// this is a 4-Bit-Counter
// 
// registered outputs are signed with the postfix .R
// 
// 
//  Pin 'Set' HIGH while clock signal (LOW-HIGH) at pin 'Clock':
//         load Q0-Q3 with state of D0-D3
// 
//  Pin 'Clear' HIGH while clock signal:
//         Q0-Q3 are cleared
// 
//  Clock signal while pins 'Set' and 'Clear' are LOW:
//         increment counter
// 
//-----------------------------------------------------
module galcounter (
 input Clock ,
 input Set ,
 input Clear ,
 input OE ,
 input  D,
 output  counter_out 
); // End of port list
//-------------Input ports Data Type-------------------
// By rule all the input ports should be wires   
wire Clock ;
wire Set ;
wire Clear ;
wire OE ;
wire  D;
//-------------Output Ports Data Type------------------
// Output port can be a storage element (reg) or a wire
reg  counter_out ;

//------------Code Starts Here-------------------------
// Since this counter is a positive edge trigged one,
// We trigger the below block with respect to positive
// edge of the clock.
always @ (posedge Clock)
begin : COUNTER // Block Name
  // At every rising edge of clock we check if reset is active
  // If active, we load the counter output with 4'b0000
  if (Set == 1'b1) begin
    counter_out <= #1 D;
  end
  else if (Clear == 1'b1) begin
    counter_out <= #1 1'b0000;
  // If enable is active, then we increment the counter
  end
  else if (OE == 1'b0) begin
    counter_out <= #1 counter_out + 1;
  end
end // End of Block COUNTER

endmodule // End of Module counter

module device( inout [28:0] P);

galcounter U_counter(
	P[1], P[6],P[7],P[13],P[2],P[18]
);
endmodule
