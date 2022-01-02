import re
import sys
import time


if len(sys.argv) < 2:
    sys.exit("No program file name given.")

program_file = sys.stdin if sys.argv[1] == "-" else open(sys.argv[1])

calculate_phi = False
starting_state = None
if len(sys.argv) > 2:
    if sys.argv[2] == "phi":
        import numpy
        import pyphi
        calculate_phi = True
    else:
        starting_state = int(sys.argv[2], base=2)

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


def stash_causation(I, target, active_reads, causation):
    reads = active_reads[I]
    result = set()
    for key in reads:
        values = reads[key]
        if len(values) == 1:
            source = program[key][1]
            result.add(source)
    causation[target] = result


class Crash(Exception):
    pass


class Computer:
    def __init__(self, A, B, I, write_callback=None):
        self.A = A
        self.B = B
        self.I = I
        self.__write_callback = write_callback

    def micro_step(self):
        instruction = program[self.I]
        operation = instruction[0]
        operand = instruction[1]
        if operation == "JMP":
            if operand == 0:
                self.A = self.B
                delta_I = None
            else:
                delta_I = operand
        else:
            bit = 1 << (bits - operand - 1)
            if operation == "SKZ":
                if self.A & bit:
                    delta_I = 1
                else:
                    delta_I = 2
            else:
                if self.__write_callback:
                    self.__write_callback(self.I, operand)
                if operation == "SET":
                    self.B |= bit
                else:
                    assert operation == "CLR"
                    self.B &= ~bit
                delta_I = 1
        if delta_I is None:
            self.I = 0
        elif self.I + delta_I <= 255:
            self.I += delta_I
        else:
            raise Crash


def next_state(prev_state, write_callback=None):
    computer = Computer(prev_state, prev_state, 0, write_callback)
    count = 0
    while True:
        count += 1
        try:
            computer.micro_step()
        except Crash:
            return None, count
        if computer.I == 0:
            return computer.A, count


def run_from(state):
    try:
        while state is not None:
            print(f"\r{state:0{bits}b}", end="")
            state, count = next_state(state)
            time.sleep(count * .1)
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


def split_state(state):
    return [int(c) for c in f"{state:0{bits}b}"]


def reorder(big_endian):
    little_endian = []
    for i in range(2 ** bits):
        le = f"{i:0{bits}b}"
        be = le[::-1]
        little_endian.append(big_endian[int(be, base=2)])
    return little_endian


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
    transitions = []
    for initial_state in range(2 ** bits):
        causation = {key: {key} for key in range(bits)}
        following_state, count = next_state(
            initial_state,
            lambda i, target: stash_causation(
                i, target, active_reads, causation
            ),
        )
        transitions.append((following_state, count))
        for target in causation:
            for source in causation[target]:
                connectivity[source][target] = 1
    if calculate_phi:
        network = pyphi.Network(
            tpm=numpy.array(reorder([split_state(s) for s, c in transitions])),
            cm=numpy.array(connectivity),
        )
    print("Transition table:")
    for initial_state in range(2 ** bits):
        following_state, count = transitions[initial_state]
        line = f"{initial_state:0{bits}b} -> "
        if following_state is None:
            line += "crash"
        else:
            line += f"{following_state:0{bits}b}"
        line += f" in {count:2} micro steps"
        if calculate_phi:
            state_array = split_state(initial_state)
            try:
                phi = pyphi.compute.phi(pyphi.Subsystem(network, state_array))
                line += f" (phi = {phi})"
            except pyphi.exceptions.StateUnreachableError:
                line += " (unreachable)"
        print(line)
    print()
    print("Connectivity matrix:")
    for row in connectivity:
        print("[" + ", ".join([str(value) for value in row]) + "]")


if starting_state is not None:
    run_from(starting_state)
else:
    analyze()
