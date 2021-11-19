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


def stash_causation(i, target, active_reads, causation):
    if active_reads is not None:
        result = set()
        for key in active_reads[i]:
            values = active_reads[i][key]
            if len(values) == 1:
                source = program[key][1]
                result.add(source)
        causation[target] = result


def next_state(prev_state, active_reads=None, causation=None):
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
            stash_causation(I, operand, active_reads, causation)
            B = B | (1 << bit)
            I = I + 1
        else:
            assert operation == "CLR"
            stash_causation(I, operand, active_reads, causation)
            B = B & ~(1 << bit)
            I = I + 1
        if I > 255:
            return None
        if I == 0:
            return B


def run_from(state):
    try:
        while state is not None:
            print(f"\r{state:0{bits}b}", end="")
            time.sleep(1)
            state = next_state(state)
        print("\rcrash" + (" " * (bits - 5)))
    except KeyboardInterrupt:
        print()


def propagate_reads(active_reads, from_index, to_index, add_value=None):
    if from_index < to_index < 256:
        from_reads = active_reads[from_index]
        to_reads = active_reads[to_index]
        for key in from_reads:
            to_reads[key] = to_reads.get(key, set()) | from_reads[key]
        if add_value is not None:
            to_reads[from_index] = to_reads.get(from_index, set()) | {add_value}


def analyze():
    active_reads = [{} for _ in range(256)]
    for i in range(256):
        instruction = program[i]
        operation = instruction[0]
        operand = instruction[1]
        if operation == "JMP":
            propagate_reads(active_reads, i, i + operand)
        elif operation == "SKZ":
            propagate_reads(active_reads, i, i + 1, 1)
            propagate_reads(active_reads, i, i + 2, 0)
        else:
            propagate_reads(active_reads, i, i + 1)
    connectivity = [[0 for _ in range(bits)] for _ in range(bits)]
    for initial_state in range(2 ** bits):
        causation = {key: {key} for key in range(bits)}
        following_state = next_state(initial_state, active_reads, causation)
        for target in causation:
            for source in causation[target]:
                connectivity[source][target] = 1
        if following_state is None:
            print(f"{initial_state:0{bits}b} -> crash")
        else:
            print(f"{initial_state:0{bits}b} -> {following_state:0{bits}b}")
    print()
    for row in connectivity:
        print("".join([str(value) for value in row]))


if starting_state is not None:
    run_from(starting_state)
else:
    analyze()
