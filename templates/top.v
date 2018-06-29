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

{% for reg, port in regs.iteritems() %}
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

{% for fun, add in add.iteritems() %}
always @(posedge clk)
begin
	{{ add['out'] }} <= {{ add['in1'] }} + {{ add['in2'] }};
end
{% endfor %}

{% for fun, mul in mul.iteritems() %}
always @(posedge clk)
begin
	{{ mul['out'] }} <= {{ mul['in1'] }} * {{ mul['in2'] }};
end
{% endfor %}

{% for fun, mov in mov.iteritems() %}
always @(posedge clk)
begin
	{{ mov['out'] }} <= {{ mov['in1'] }};
end
{% endfor %}


{% for fun, m in mux.iteritems() %}
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
		{% for k, v in fsm.iteritems() %}
			{{ k }}:
			begin
			    {% for sig, val in fsm[k]['signals'].iteritems() %}
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
