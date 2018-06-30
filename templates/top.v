/*
* This is top module
*/

module top
( 
	input clk, reset
);

{% for asig in all_signals %}
wire {{ bit_range }} {{ asig }};
{% endfor %}

{% for reg in regs %}
reg {{ bit_range }} {{ reg }};
{% endfor %}

{% for reg, port in regs.items() %}
always @(posedge clk)
begin
	if (~reset)
		{{ reg }} <= 0;
	else begin
		{{ reg }} <= {{ port['in'] }};
		{{ port['out'] }} <= {{ reg }};
	end
end
{% endfor %}

{% for fun, add in add.items() %}
assign {{ add['out'] }} <= {{ add['in1'] }} + {{ add['in2'] }};
{% endfor %}

{% for fun, mul in mul.items() %}
assign {{ mul['out'] }} <= {{ mul['in1'] }} * {{ mul['in2'] }};
{% endfor %}

{% for fun, mov in mov.items() %}
assign {{ mov['out'] }} <= {{ mov['in1'] }};
{% endfor %}


{% for fun, m in mux.items() %}
always @(posedge clk)
begin
    case( {{ fun }} )
        0: {{ m['out'] }} <= {{ m['in0'] }};
        1: {{ m['out'] }} <= {{ m['in1'] }};
    endcase
end
{% endfor %}

{% if fsm %}
always @(posedge clk)
begin
	reg {{ bit_range }} state;
	if (~reset) 
		state <= 0;
	else begin
		case( state )
		{% for k, v in fsm.items() %}
			{{ k }}:
			begin
			    {% for sig, val in fsm[k]['signals'].items() %}
				{{ sig }} <= {{ val }};
			    {% endfor %}
				state <= {{ v['next_state'] }};
			end
		{% endfor %}
	endcase
	end
end
{% endif %}



endmodule
