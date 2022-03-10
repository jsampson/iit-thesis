#!/usr/bin/env python3
#
# Justin's IIT Thesis - Toy Computer Emulator
# Copyright 2022 by Justin T. Sampson
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
    if sys.argv[2] == "diagram":
        command = "diagram"
    elif sys.argv[2] == "micro":
        command = "micro"
    else:
        command = "run"
        starting_state = int(sys.argv[2], base=2)
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


class Analyzer:
    def __init__(self):
        self.active_reads = [{} for _ in range(256)]
        self.bb_candidates = [(set(), set()) for _ in range(256)]
        self.connectivity = [[0 for _ in range(bits)] for _ in range(bits)]
        self.transitions = []

    def perform_analysis(self):
        for i in range(256):
            instruction = program[i]
            operation = instruction[0]
            operand = instruction[1]
            if operation == "JMP":
                self.propagate_reads(i, i + operand)
            elif operation == "SKZ":
                self.propagate_reads(i, i + 1, 1)
                self.propagate_reads(i, i + 2, 0)
            else:
                self.propagate_reads(i, i + 1)
                self.propagate_write(i)
        for initial_state in range(2 ** bits):
            causation = {key: {key} for key in range(bits)}
            following_state, count = next_state(
                initial_state,
                lambda i, target: self.stash_causation(i, target, causation),
            )
            self.transitions.append((following_state, count))
            for target in causation:
                for source in causation[target]:
                    self.connectivity[source][target] = 1

    def stash_causation(self, I, target, causation):
        reads = self.active_reads[I]
        result = set()
        for key in reads:
            values = reads[key]
            if (len(values[0]) == 0) ^ (len(values[1]) == 0):
                source = program[key][1]
                result.add(source)
        causation[target] = result

    def propagate_reads(self, from_index, to_index, add_value=None):
        if from_index < to_index < 256:
            from_reads = self.active_reads[from_index]
            to_reads = self.active_reads[to_index]
            for key in from_reads:
                self.add_to_reads(to_reads, key, 0,
                    [path + [from_index] for path in from_reads[key][0]]
                )
                self.add_to_reads(to_reads, key, 1,
                    [path + [from_index] for path in from_reads[key][1]]
                )
            if add_value is not None:
                self.add_to_reads(to_reads, from_index, add_value, [[from_index]])

    def add_to_reads(self, to_reads, key, value, new_paths):
        if key in to_reads:
            value_paths = to_reads[key]
        else:
            value_paths = ([], [])
            to_reads[key] = value_paths
        value_paths[value].extend(new_paths)

    def propagate_write(self, target):
        target_instruction = program[target]
        target_operand = target_instruction[1]
        reads_at_write = self.active_reads[target]
        self.bb_candidates[target][1].add(target_operand)
        for source in reads_at_write:
            if_0, if_1 = reads_at_write[source]
            if (len(if_0) == 0) ^ (len(if_1) == 0):
                source_instruction = program[source]
                source_operand = source_instruction[1]
                self.bb_candidates[target][0].add(source_operand)
                paths = if_0 or if_1
                for path in paths:
                    for i in path:
                        self.bb_candidates[i][0].add(source_operand)
                        self.bb_candidates[i][1].add(target_operand)


def split_state(state, b=bits):
    return [int(c) for c in f"{state:0{b}b}"]


def reorder(big_endian, b=bits):
    little_endian = []
    for i in range(2 ** b):
        le = f"{i:0{b}b}"
        be = le[::-1]
        little_endian.append(big_endian[int(be, base=2)])
    return little_endian


def analyze():
    a = Analyzer()
    a.perform_analysis()
    if calculate_phi:
        network = pyphi.Network(
            tpm=numpy.array(reorder([split_state(s) for s, c in a.transitions])),
            cm=numpy.array(a.connectivity),
        )
    print("Transition table:")
    for initial_state in range(2 ** bits):
        following_state, count = a.transitions[initial_state]
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
    i_bits = int.bit_length(program_length)
    total_bits = 2 * bits + i_bits
    transitions = []
    for a in range(2 ** bits):
        for b in range(2 ** bits):
            for i in range(2 ** i_bits):
                computer = Computer(a, b, i)
                try:
                    computer.micro_step()
                except Crash:
                    pass  # The registers are correct even when crashing.
                assert computer.A < 2 ** bits
                assert computer.B < 2 ** bits
                if computer.I >= 2 ** i_bits:
                    sys.exit("I exceeded given program length.")
                transitions.append(
                    (computer.A << (bits + i_bits))
                    | (computer.B << i_bits)
                    | computer.I
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
    print("Micro transition table:")
    for initial_state in range(2 ** total_bits):
        following_state = transitions[initial_state]
        print(
            f"{initial_state:0{total_bits}b} -> {following_state:0{total_bits}b}"
        )
    print()
    print("Micro connectivity matrix:")
    for row in connectivity:
        print("[" + ", ".join([str(value) for value in row]) + "]")
    if calculate_phi:
        print()
        network = pyphi.Network(
            tpm=numpy.array(
                reorder(
                    [split_state(s, total_bits) for s in transitions],
                    total_bits,
                )
            ),
            cm=numpy.array(connectivity),
        )
        for a in range(2 ** bits):
            state = (a << (bits + i_bits)) | (a << i_bits)
            state_array = split_state(state, total_bits)
            print(f"Computing phi for {state:0{total_bits}b}...")
            try:
                phi = pyphi.compute.phi(pyphi.Subsystem(network, state_array))
                print(f"* Phi = {phi}")
            except pyphi.exceptions.StateUnreachableError:
                print("* Unreachable")


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
    print("\\draw (-4,1.25) node{Instruction on path\\ldots};")
    print("\\draw (-4,.75) node[anchor=east]{from reads of:};")
    print("\\draw (-3.625,.75) node[anchor=west]{to writes of:};")
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
        print(f"\\draw (-4,{-.75*i}) node[{rdraw}anchor=east](r{i}){{{reads}}};")
        print(f"\\draw (-3.625,{-.75*i}) node[{wdraw}anchor=west](w{i}){{{writes}}};")
        print(f"\\draw[->,ultra thin] (r{i}) edge (w{i});")
        print(f"\\draw[ultra thin,dotted] (w{i}) -- (i{i});")
    print(r"\end{tikzpicture}")


if command == "run":
    run_from(starting_state)
elif command == "analyze":
    analyze()
elif command == "diagram":
    diagram()
else:
    assert command == "micro"
    micro_analyze()
