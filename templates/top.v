/*
* This is top module
*/

module top
( 
	input clk, reset
)

{% for reg in regs %}
register reg_{{ reg }}
(
input {{ reg }}
)
{% endfor %}

{% for add in add %}
full_adder add_{{ add }}
{% endfor %}

{% for mul in mul %}
multiplier mul_{{ mul }}
{% endfor %}

{% for mov in mov %}
move mov_{{ mov }}
{% endfor %}

{% for m in mux %}
mux mux_{{ m }}
{% endfor %}

case state:
{% for k, v in fsm.iteritems() %}
{{ k }}:
    {% for sig, val in fsm[k]['signals'].iteritems() %}
        {{ sig }} = {{ val }}
    {% endfor %}
{% endfor %}



endmodule
