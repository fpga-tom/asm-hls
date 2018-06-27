/* 
* This is register
*/

module register
(
	input clk, reset,
	input d,
	output q;
)

always @(posedge clk)
	if (reset) begin
		q <= 1'b0;
	end else begin
		q <= d;
	end
endmodule

