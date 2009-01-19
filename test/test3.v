//-----------------------------------------------------
// 
//-----------------------------------------------------
module test (
 input  D,
 input  F,
 input  G,
 input  H,
 input  I,
 output  Q 
); // End of port list
//-------------Input ports Data Type-------------------
// By rule all the input ports should be wires   
wire D;
//-------------Output Ports Data Type------------------
// Output port can be a storage element (reg) or a wire
wire Q ;

//------------Code Starts Here-------------------------
// Since this counter is a positive edge trigged one,
// We trigger the below block with respect to positive
// edge of the clock.
assign	Q = (^ D) | F | G | H | I;

endmodule // End of Module counter

module device( inout [28:0] P);

test U_test(
	P[1], P[2], P[3], P[4], P[5], P[6]
);
endmodule