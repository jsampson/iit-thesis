import re
import sys
import time


if len(sys.argv) < 2:
    sys.exit("No program file name given.")

program_file = sys.stdin if sys.argv[1] == "-" else open(sys.argv[1])

starting_state = None if len(sys.argv) < 3 else int(sys.argv[2], base=2)

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

for line in program_file:
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


def next_state(prev_state):
    A = prev_state
    B = prev_state
    I = 0
    while True:
        instruction = program[I]
        operation = instruction[0]
        operand = instruction[1]
        bit = bits - operand - 1
        if operation == "JMP":
            if operand == 0:
                I = 0
            else:
                I = I + operand
        elif operation == "SKZ":
            if A & (1 << bit):
                I = I + 1
            else:
                I = I + 2
        elif operation == "SET":
            B = B | (1 << bit)
            I = I + 1
        else:
            assert operation == "CLR"
            B = B & ~(1 << bit)
            I = I + 1
        if I > 255:
            return None
        if I == 0:
            return B


if starting_state is not None:
    state = starting_state
    try:
        while state is not None:
            print(f"\r{state:0{bits}b}", end="")
            time.sleep(.5)
            state = next_state(state)
        print("\rcrash" + (" " * (bits - 5)))
    except KeyboardInterrupt:
        print()
else:
    for initial_state in range(2 ** bits):
        following_state = next_state(initial_state)
        if following_state is None:
            print(f"{initial_state:0{bits}b} -> crash")
        else:
            print(f"{initial_state:0{bits}b} -> {following_state:0{bits}b}")
