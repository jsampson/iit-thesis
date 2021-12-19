import operator

from fractions import Fraction as F
from functools import reduce
from sys import argv

from gate import Gate
from path_runner import PathRunner


def AND(inputs):
    return all(inputs)

def OR(inputs):
    return any(inputs)

def COPY(inputs):
    assert len(inputs) == 1
    return inputs[0]

def NOT(inputs):
    assert len(inputs) == 1
    return not inputs[0]

def XOR(inputs):
    return reduce(operator.xor, inputs, False)

def NAND(inputs):
    return not all(inputs)


if argv[1] == "idealized.tex":
    gates = [
        Gate([1, 2], True,  (1, 0, 0), OR, "P"),
        Gate([2],    False, (1, 0, 0), COPY, "Q"),
        Gate([0, 1], False, (1, 0, 0), XOR, "R"),
    ]
    width = F(5)
    height = F(4)
    padding = F(1, 5)
    end_time = F(40)
elif argv[1] == "jagged.tex":
    gates = [
        Gate([1, 2], True,  ("1.0", "1.01"), OR, "P"),
        Gate([2],    False, ("0.5", "1.01"), COPY, "Q"),
        Gate([0, 1], False, ("1.5", "1.01"), XOR, "R"),
    ]
    width = F(5)
    height = F(4)
    padding = F(1, 5)
    end_time = F(40)
elif argv[1] == "flatline.tex":
    gates = [
        Gate([1, 2], True,  ("1.0", "1.0208333333334"), OR, "P"),
        Gate([2],    False, ("0.5", "1.0208333333334"), COPY, "Q"),
        Gate([0, 1], False, ("1.5", "1.0208333333334"), XOR, "R"),
    ]
    width = F(5)
    height = F(4)
    padding = F(1, 5)
    end_time = F(40)
elif argv[1] == "clocked.tex":
    FLIP_FLOP_GATES = 7
    FLIP_FLOP_OUTPUT = 4
    def create_flip_flop(gates, clock, data, value, label):
        offset = len(gates)
        gates.append(Gate([offset + 3, offset + 1], value,     (1, "1.0208333333334"), NAND))
        gates.append(Gate([offset, clock],          True,      (1, "1.0208333333334"), NAND))
        gates.append(Gate([offset + 6, offset + 3], True,   (".9", "1.0208333333334"), NAND))
        gates.append(Gate([offset + 2, data],       not value, (1, "1.0208333333334"), NAND))
        gates.append(Gate([offset + 1, offset + 5], value,     (1, "1.0208333333334"), NAND, label))
        gates.append(Gate([offset + 4, offset + 2], not value, (1, "1.0208333333334"), NAND))
        gates.append(Gate([offset + 1, clock],      False,  (".1", 0), AND))  # fan-in for offset + 2
    clock = 0
    gateP = 1
    gateQ = 2
    gateR = 3
    ffOffsetP = 4
    ffOffsetQ = ffOffsetP + FLIP_FLOP_GATES
    ffOffsetR = ffOffsetQ + FLIP_FLOP_GATES
    ffOutputP = ffOffsetP + FLIP_FLOP_OUTPUT
    ffOutputQ = ffOffsetQ + FLIP_FLOP_OUTPUT
    ffOutputR = ffOffsetR + FLIP_FLOP_OUTPUT
    gates = []
    gates.append(Gate([clock], False, (10, 0, 0), NOT, "clock"))
    gates.append(Gate([ffOutputQ, ffOutputR], False, ("1.0", "1.0208333333334"), OR))
    gates.append(Gate([ffOutputR],            False, ("0.5", "1.0208333333334"), COPY))
    gates.append(Gate([ffOutputP, ffOutputQ], False, ("1.5", "1.0208333333334"), XOR))
    create_flip_flop(gates, clock, gateP, True, "P")
    create_flip_flop(gates, clock, gateQ, False, "Q")
    create_flip_flop(gates, clock, gateR, False, "R")
    width = F(5)
    height = F(5)
    padding = F(1, 5)
    end_time = F(240)
else:
    raise ValueError


runner = PathRunner(gates)
runner.truncate_at(end_time)

paths_to_display = []
path_names = []
for i in range(0, len(gates)):
    gate = gates[i]
    if gate.label is not None:
        paths_to_display.append(i)
        path_names.append(gate.label)

size = len(paths_to_display)
time = runner.get_time()

path_width = width - 2 * padding
path_height = (height - padding) / size - padding

print("\\begin{tikzpicture}")

for i in range(0, size):
    path_bottom = height - (padding + path_height) * (i + 1)
    path_middle = path_bottom + path_height / 2

    print("\\draw[very thin] (%f,%f) node[anchor=east]{%s} -- (%f,%f);"
            % (padding, path_middle, path_names[i],
               padding + path_width, path_middle))

    path = runner.get_path(paths_to_display[i])
    for p in range(0, len(path)):
        point_t, point_v = path[p]
        x = point_t * path_width / time + padding
        y = point_v * path_height + path_bottom
        if p == 0:
            print("\\draw ", end="")
        else:
            print(" -- ", end="");
        print("(%f,%f)" % (x, y), end="")
    print(";")

print("\\end{tikzpicture}")
