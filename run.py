import re
import sys


LINE = re.compile("^\\s*([A-Z]+)\\s*(?:([#+])\\s*([0-9]+)\\s*)?$", re.IGNORECASE)

OPS = {
    "JMP": "+",
    "SKZ": "#",
    "SET": "#",
    "CLR": "#",
    "END": None,
    "NOP": None
}

program = []
bits = 0

for line in sys.stdin:
    if not line or line.isspace():
        continue
    match = LINE.fullmatch(line)
    if match is None:
        sys.exit("Invalid line: " + line)
    operation = match.group(1).upper()
    operand_prefix = match.group(2)
    if operation not in OPS:
        sys.exit("Invalid operation: " + line)
    if operand_prefix != OPS[operation]:
        sys.exit("Invalid operand prefix: " + line)
    if operand_prefix:
        operand_value = int(match.group(3))
        if operand_value > 63:
            sys.exit("Invalid operand value: " + line)
        program.append((operation, operand_value))
        if operand_prefix == "#" and operand_value > bits - 1:
            bits = operand_value + 1
    elif operation == "END":
        program.append(("JMP", 0))
    else:
        assert operation == "NOP"
        program.append(("JMP", 1))

if len(program) > 256:
    sys.exit(f"Program too long: {len(program)} instructions")

while len(program) < 256:
    program.append(("JMP", 0))

for initial_state in range(2 ** bits):
    A = initial_state
    B = initial_state
    I = 0
    while True:
        instruction = program[I]
        operation = instruction[0]
        operand = instruction[1]
        if operation == "JMP":
            if operand == 0:
                I = 0
            else:
                I = I + operand
        elif operation == "SKZ":
            if A & (1 << operand):
                I = I + 1
            else:
                I = I + 2
        elif operation == "SET":
            B = B | (1 << operand)
            I = I + 1
        else:
            assert operation == "CLR"
            B = B & ~(1 << operand)
            I = I + 1
        if I > 255:
            sys.exit(f"Crashed for input {initial_state}")
        if I == 0:
            print(f"{A:0{bits}b} -> {B:0{bits}b}")
            break
