#!/usr/bin/env python3
#
# Justin's IIT Thesis - Toy Computer Emulator
# Copyright 2022-2023 by Justin T. Sampson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import json
import re
import sys
import time


if len(sys.argv) < 2:
    sys.exit("No program file name given.")

program_file = sys.stdin if sys.argv[1] == "-" else open(sys.argv[1])

calculate_phi = False
if len(sys.argv) > 2 and sys.argv[-1] == "phi":
    import numpy
    import pyphi
    del sys.argv[-1]
    calculate_phi = True

if len(sys.argv) > 2:
    if sys.argv[2] == "optimize":
        command = "optimize"
    elif sys.argv[2] == "diagram":
        command = "diagram"
    elif sys.argv[2] == "micro":
        command = "micro"
        micro_state = sys.argv[3] if len(sys.argv) > 3 else None
    elif sys.argv[2] == "test":
        command = "test"
        test_stage = sys.argv[3]
        if test_stage not in ("prep", "check"):
            sys.exit("Test stage must be 'prep' or 'check', not '{test_stage}'.")
    else:
        command = "run"
        starting_state = sys.argv[2]
else:
    command = "analyze"

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

program_length = len(program)
while len(program) < 256:
    program.append(("JMP", 0))

zeroes = [0]*bits


class Crash(Exception):
    pass


class Computer:
    def __init__(self, A, B, I):
        self.A = A.copy()  # list of int (0 or 1)
        self.B = B.copy()  # list of int (0 or 1)
        self.I = I         # int

    def micro_step(self):
        instruction = program[self.I]
        operation = instruction[0]
        operand = instruction[1]
        if operation == "JMP":
            if operand == 0:
                self.A[:] = self.B
                self.B[:] = zeroes
                delta_I = None
            else:
                delta_I = operand
        else:
            if operation == "SKZ":
                if self.A[operand]:
                    delta_I = 1
                else:
                    delta_I = 2
            else:
                if operation == "SET":
                    self.B[operand] = 1
                else:
                    assert operation == "CLR"
                    self.B[operand] = 0
                delta_I = 1
        if delta_I is None:
            self.I = 0
        elif self.I + delta_I <= 255:
            self.I += delta_I
        else:
            raise Crash


def next_state(prev_state):
    computer = Computer(prev_state, zeroes, 0)
    count = 0
    while True:
        count += 1
        try:
            computer.micro_step()
        except Crash:
            return None, count
        if computer.I == 0:
            return computer.A, count


def run_from(state_str):
    state = str_to_state(state_str, bits)
    try:
        while state is not None:
            print(f"\r{state_to_str(state)}", end="")
            state, count = next_state(state)
            time.sleep(count * .1)
        print("\rcrash" + (" " * (bits - 5)))
    except KeyboardInterrupt:
        print()


class Analyzer:
    def __init__(self):
        self.bb_candidates = [(set(), set()) for _ in range(256)]
        self.connectivity = [[0 for _ in range(bits)] for _ in range(bits)]
        self.transitions = []

    def perform_analysis(self):
        ended_paths = []
        crashed_paths = []

        for initial_state in gen_states():
            computer = Computer(initial_state, zeroes, 0)
            path = []
            while True:
                path.append(computer.I)
                try:
                    computer.micro_step()
                except Crash:
                    following_state = None
                    break
                if computer.I == 0:
                    following_state = computer.A
                    break
            self.transitions.append((initial_state, following_state, len(path)))
            (crashed_paths if following_state is None else ended_paths).append(path)

        paths_per_read_per_inst = [[0 for _ in range(256)] for _ in range(256)]

        for path in ended_paths + crashed_paths:
            reads = []
            for i in path:
                if program[i][0] == "SKZ":
                    reads.append(i)
                for r in reads:
                    paths_per_read_per_inst[i][r] += 1

        for path in ended_paths:
            reads = []
            for i in path:
                reads = [
                    r for r in reads
                    if paths_per_read_per_inst[i][r] != paths_per_read_per_inst[r][r]
                ]
                operation = program[i][0]
                if operation == "SKZ":
                    reads.append(i)
                elif operation == "SET" or operation == "CLR":
                    target = program[i][1]
                    self.bb_candidates[i][1].add(target)
                    for r in reads:
                        source = program[r][1]
                        self.connectivity[source][target] = 1
                        for x in path:
                            if r <= x <= i:
                                self.bb_candidates[x][0].add(source)
                                self.bb_candidates[x][1].add(target)


def int_to_state(state_int, b=bits):
    return [int(bool(state_int & (1 << i))) for i in range(b)]


def state_to_int(state):
    result = 0
    for i in range(len(state)):
        if state[i]:
            result += 2**i
    return result


def str_to_state(state_str, b=bits):
    if not re.fullmatch(f"[01]{{{b}}}", state_str):
        sys.exit(f"Given state <{state_str}> should be {b} bits.")
    return [int(s) for s in state_str]


def state_to_str(state):
    return "".join([str(s) for s in state])


def gen_states(b=bits):
    for i in range(2**b):
        yield int_to_state(i, b)


def analyze():
    a = Analyzer()
    a.perform_analysis()
    if calculate_phi:
        network = pyphi.Network(
            tpm=numpy.array([t for s, t, c in a.transitions]),
            cm=numpy.array(a.connectivity),
        )
    print("Transition table:")
    for initial_state, following_state, count in a.transitions:
        line = f"{state_to_str(initial_state)} -> "
        if following_state is None:
            line += "crash"
        else:
            line += f"{state_to_str(following_state)}"
        line += f" in {count:2} micro steps"
        if calculate_phi:
            try:
                phi = pyphi.compute.phi(pyphi.Subsystem(network, initial_state))
                line += f" (phi = {phi})"
            except pyphi.exceptions.StateUnreachableError:
                line += " (unreachable)"
        print(line)
    print()
    print("Connectivity matrix:")
    for row in a.connectivity:
        print("[" + ", ".join([str(value) for value in row]) + "]")
    print()
    print("Hypothetical black-box assignments:")
    assignments = []
    for i in range(256):
        instruction = program[i]
        operation = instruction[0]
        operand = instruction[1]
        if operation == "JMP" and operand == 0:
            printable = "END"
        elif operation == "JMP" and operand == 1:
            printable = "NOP"
        else:
            printable = f"{operation} {OPS[operation]}{operand}"
        bb_reads, bb_writes = a.bb_candidates[i]
        if len(bb_writes) == 1:
            assignment = next(iter(bb_writes))
        elif len(bb_reads) == 1:
            assignment = next(iter(bb_reads))
        elif len(bb_writes) > 1 and len(bb_reads) > 1:
            assignment = "?"
        else:
            assignment = "-"
        assignments.append((printable, assignment))
    last_i = -1
    for i in range(255, -1, -1):
        if assignments[i] != ("END", "-"):
            last_i = i
            break
    for i in range(0, min(256, last_i + 2)):
        printable, assignment = assignments[i]
        print(f"{printable: <8}->{assignment: >3}")


def micro_analyze():
    i_bits = int.bit_length(program_length-1)
    total_bits = 2 * bits + i_bits
    transitions = []
    for abi in gen_states(total_bits):
        a = abi[0:bits]
        b = abi[bits:2*bits]
        i = state_to_int(abi[2*bits:])
        computer = Computer(a, b, i)
        try:
            computer.micro_step()
        except Crash:
            pass  # The registers are correct even when crashing.
        assert len(computer.A) == bits
        assert len(computer.B) == bits
        if computer.I >= 2 ** i_bits:
            sys.exit("I exceeded given program length.")
        transitions.append(
            (abi, computer.A + computer.B + int_to_state(computer.I, i_bits))
        )
    connectivity = [[0 for _ in range(total_bits)] for _ in range(total_bits)]
    a_indexes = range(0, bits)
    b_indexes = range(bits, 2 * bits)
    i_indexes = range(2 * bits, total_bits)
    for row in a_indexes:
        connectivity[row][row] = 1
        for col in i_indexes:
            connectivity[row][col] = 1
    for row in b_indexes:
        connectivity[row][row] = 1
        connectivity[row][row - bits] = 1
    for row in i_indexes:
        for col in a_indexes:
            connectivity[row][col] = 1
        for col in b_indexes:
            connectivity[row][col] = 1
        for col in i_indexes:
            connectivity[row][col] = 1
    if calculate_phi:
        print()
        network = pyphi.Network(
            tpm=numpy.array([t for s, t in transitions]),
            cm=numpy.array(connectivity),
        )
        for state_array in (
            [str_to_state(micro_state, total_bits)]
            if micro_state
            else gen_states(total_bits)
        ):
            print(f"Computing phi for {state_to_str(state_array)}...")
            try:
                phi = pyphi.compute.phi(pyphi.Subsystem(network, state_array))
                print(f"* Phi = {phi}")
            except pyphi.exceptions.StateUnreachableError:
                print("* Unreachable")
    else:
        print("import numpy")
        print("import pyphi")
        print()
        print("tpm = [")
        for initial_state, following_state in transitions:
            print("    [" + ", ".join([str(value) for value in following_state]) + "],", end="")
            print("  # <- [" + ", ".join([str(value) for value in initial_state]) + "]")
        print("]")
        print()
        print("cm = [")
        for row in connectivity:
            print("    [" + ", ".join([str(value) for value in row]) + "],")
        print("]")
        print()
        state = str_to_state(micro_state, total_bits) if micro_state else [0]*total_bits
        print("state = [" + ", ".join([str(value) for value in state]) + "]")
        print()
        print("network = pyphi.Network(tpm=numpy.array(tpm), cm=numpy.array(cm))")
        print("subsystem = pyphi.Subsystem(network, state)")
        print()
        print("try:")
        print("    phi = pyphi.compute.phi(subsystem)")
        print("    print(f\"Phi = {phi}\")")
        print("except pyphi.exceptions.StateUnreachableError:")
        print("    print(\"Unreachable\")")


def diagram():
    a = Analyzer()
    a.perform_analysis()
    print(r"\begin{tikzpicture}[scale=.5, transform shape, line cap=rect]")
    last = 0
    edges = []
    for i in range(256):
        if i > last:
            break
        instruction = program[i]
        operation = instruction[0]
        operand = instruction[1]
        print(f"\\draw (0,{-.75*i}) node[anchor=east](i{i}){{{i}.}};")

        if operation == "JMP" and operand == 0:
            print(f"\\draw (0,{-.75*i}) node[fill=lightgray,anchor=west](o{i}){{\\texttt{{END}}}};")
            furthest = 0
        elif operation == "JMP" and operand == 1:
            print(f"\\draw (0,{-.75*i}) node[anchor=west](o{i}){{\\texttt{{NOP}}}};")
            edges.append(f"\\draw[->,ultra thin] (o{i}) edge (o{i+1});")
            furthest = i + 1
        else:
            print(f"\\draw (0,{-.75*i}) node[anchor=west](o{i}){{\\texttt{{{operation}}}}};")
            punct = OPS[operation].replace("#", r"\#")
            print(f"\\draw (o{i}.east) node[anchor=west](x{i}){{\\texttt{{{punct}{operand}}}}};")
            if operation == "SKZ":
                edges.append(f"\\draw[->,ultra thin] (o{i}) edge (o{i+1});")
                edges.append(f"\\draw[->,ultra thin] (i{i}) edge[out=210,in=150] (i{i+2});")
                furthest = i + 2
            elif operation == "JMP":
                target = program[i + operand]
                x = "x" if target[0] != "JMP" or target[1] > 1 else "o"
                edges.append(f"\\draw[->,ultra thin] (x{i}) edge[out=0,in=0] ({x}{i+operand});")
                furthest = i + operand
            else:
                edges.append(f"\\draw[->,ultra thin] (o{i}) edge (o{i+1});")
                furthest = i + 1
        if furthest > last:
            last = furthest
    for edge in edges:
        print(edge)
    max_writes = max(len(bb[1]) for bb in a.bb_candidates)
    bb_offset = min(-4, -max_writes-1)
    print(f"\\draw ({bb_offset},1.25) node{{Instruction on path\\ldots}};")
    print(f"\\draw ({bb_offset},.75) node[anchor=east]{{from reads of:}};")
    print(f"\\draw ({bb_offset+.375},.75) node[anchor=west]{{to writes of:}};")
    for i in range(0, last+1):
        bb = a.bb_candidates[i]
        reads, writes = (
            ", ".join(f"\\texttt{{\\#{n}}}" for n in sorted(s))
            if s
            else "$\\varnothing$"
            for s in bb
        )
        rdraw = ""
        wdraw = ""
        if len(bb[1]) == 1:
            wdraw = "draw,ultra thin,"
        elif len(bb[0]) == 1:
            rdraw = "draw,ultra thin,"
        print(f"\\draw ({bb_offset},{-.75*i}) node[{rdraw}anchor=east](r{i}){{{reads}}};")
        print(f"\\draw ({bb_offset+.375},{-.75*i}) node[{wdraw}anchor=west](w{i}){{{writes}}};")
        print(f"\\draw[->,ultra thin] (r{i}) edge (w{i});")
        print(f"\\draw[ultra thin,dotted] (w{i}) -- (i{i});")
    print(r"\end{tikzpicture}")


def test_prep():
    a = Analyzer()
    a.perform_analysis()
    expected = a.transitions
    print("[")
    for i in range(len(expected)):
        print("  " + json.dumps(expected[i]) + ("," if i < len(expected)-1 else ""))
    print("]")


def test_check():
    expected = json.load(sys.stdin)
    a = Analyzer()
    a.perform_analysis()
    actual = a.transitions
    if len(actual) != len(expected):
        sys.exit(f"Expected {len(expected)} transitions but actually {len(actual)}.")
    mismatches = []
    for i in range(len(actual)):
        if expected[i][0] != actual[i][0]:
            sys.exit(f"Expected starting state {expected[i][0]} but actually {actual[i][0]}.")
        if expected[i][1] != actual[i][1]:
            mismatches.append((expected[i][0], expected[i][1], actual[i][1]))
    if len(mismatches) == 0:
        print("Test passed!")
    else:
        print("Test failed. Mismatched transitions:")
        for initial_state, expected_state, actual_state in mismatches:
            print(f"{state_to_str(initial_state)} -> {state_to_str(expected_state)} vs. {state_to_str(actual_state)}")
        sys.exit(1)


def generate_optimized_program():
    a = Analyzer()
    a.perform_analysis()
    best_program = None
    best_score = None
    for gen_program in generate_branches(a.transitions, list(range(bits)), [None for b in range(bits)]):
        gen_score = optimization_score(gen_program)
        if best_score is None or gen_score < best_score:
            best_score = gen_score
            best_program = gen_program
    for instruction in best_program:
        print(instruction)


def optimization_score(gen_program):
    return (
        len([jmp for jmp in gen_program if jmp.startswith("JMP")]),
        len(gen_program),
    )


def generate_branches(transitions, remaining_bits, bit_values):
    # number of results is F(n) = n * F(n-1)^2; F(0) = 1 --> 1, 1, 2, 12, 576, 1658880
    if remaining_bits == []:
        next_state = [t for s, t, c in transitions if s == bit_values][0]
        return [[f"SET #{bit}" for bit in range(bits) if next_state[bit]] + ["END"]]
    else:
        result = []
        for read_bit in remaining_bits:
            sub_remaining_bits = remaining_bits.copy()
            sub_remaining_bits.remove(read_bit)
            bit_values[read_bit] = 0
            left_branches = generate_branches(transitions, sub_remaining_bits, bit_values)
            bit_values[read_bit] = 1
            right_branches = generate_branches(transitions, sub_remaining_bits, bit_values)
            bit_values[read_bit] = None
            for left_branch in left_branches:
                for right_branch in right_branches:
                    result.append(combine_branches(read_bit, left_branch, right_branch))
        return result


def combine_branches(read_bit, left_branch, right_branch):
    if left_branch == right_branch:
        return left_branch

    result = []
    left_sets, left_rest = extract_set_instructions(left_branch)
    right_sets, right_rest = extract_set_instructions(right_branch)
    for s in left_sets.copy():
        if s in right_sets:
            result.append(s)
            left_sets.remove(s)
            right_sets.remove(s)

    left_branch = left_sets + left_rest
    right_branch = right_sets + right_rest

    result.append(f"SKZ #{read_bit}")

    if right_branch == ["END"]:
        result.append("END")
        result.extend(left_branch)
    elif left_branch == right_branch[1:]:
        result.extend(right_branch)
    else:
        offset = min(
            (o for o in range(1, len(left_branch)-len(right_branch)+1) if right_branch == left_branch[o:]),
            default=None
        )
        if offset is not None:
            result.append(f"JMP +{offset+1}")
            result.extend(left_branch)
        else:
            result.append(f"JMP +{len(left_branch)+1}")
            result.extend(left_branch)
            result.extend(right_branch)
    return tuple(result)


def extract_set_instructions(instructions):
    set_instructions = []
    rest_instructions = []
    in_sets = True
    for instruction in instructions:
        if in_sets and instruction.startswith("SET"):
            set_instructions.append(instruction)
        else:
            in_sets = False
            rest_instructions.append(instruction)
    return set_instructions, rest_instructions


if command == "run":
    run_from(starting_state)
elif command == "analyze":
    analyze()
elif command == "diagram":
    diagram()
elif command == "test":
    if test_stage == "prep":
        test_prep()
    else:
        test_check()
elif command == "optimize":
    generate_optimized_program()
else:
    assert command == "micro"
    micro_analyze()
