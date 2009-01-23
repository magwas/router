//-----------------------------------------------------
// 
//-----------------------------------------------------
module test1 (
 input  D,
 output  Q 
); // End of port list
//-------------Input ports Data Type-------------------
// By rule all the input ports should be wires   
wire D;
//-------------Output Ports Data Type------------------
// Output port can be a storage element (reg) or a wire
wire Q ;

//------------Code Starts Here-------------------------
assign	Q = ^ D;

endmodule // End of Module counter

module device( inout [28:0] P);

test1 U_test(
	P[1], P[2]
);
endmodule
