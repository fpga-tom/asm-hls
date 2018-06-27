/*
* This is mux
*/

module mux
(
	input din_0,
	input din_1,
	input sel,
	output mux_out
);

assign mux_out = sel ? din_1 : din_0;

endmodule
