
import parser
import visitor

## global dictionary for data
scope = {}

scope['unit'] = parser.parse("a.asm")
visitor.construct_cfg(scope)
print(scope)

