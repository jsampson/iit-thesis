import operator

from fractions import Fraction as F
from functools import reduce
from sys import argv

from gate import Gate, rel_gate
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
        Gate([1, 2], True,  F(1), F(0), F(0), OR),
        Gate([2],    False, F(1), F(0), F(0), COPY),
        Gate([0, 1], False, F(1), F(0), F(0), XOR),
    ]
    width = F(5)
    height = F(4)
    padding = F(1, 5)
    paths_to_display = [0, 1, 2]
    path_names = ["P", "Q", "R"]
    end_time = F(40)
elif argv[1] == "jagged.tex":
    gates = [
        rel_gate([1, 2], True,  F("1.0"), F("1.01"), OR),
        rel_gate([2],    False, F("0.5"), F("1.01"), COPY),
        rel_gate([0, 1], False, F("1.5"), F("1.01"), XOR),
    ]
    width = F(5)
    height = F(4)
    padding = F(1, 5)
    paths_to_display = [0, 1, 2]
    path_names = ["P", "Q", "R"]
    end_time = F(40)
elif argv[1] == "flatline.tex":
    gates = [
        rel_gate([1, 2], True,  F("1.0"), F("1.0208333333334"), OR),
        rel_gate([2],    False, F("0.5"), F("1.0208333333334"), COPY),
        rel_gate([0, 1], False, F("1.5"), F("1.0208333333334"), XOR),
    ]
    width = F(5)
    height = F(4)
    padding = F(1, 5)
    paths_to_display = [0, 1, 2]
    path_names = ["P", "Q", "R"]
    end_time = F(40)
elif argv[1] == "clocked.tex":
    FLIP_FLOP_GATES = 7
    FLIP_FLOP_OUTPUT = 4
    def create_flip_flop(gates, clock, data, value):
        offset = len(gates)
        gates.append(rel_gate([offset + 3, offset + 1], value,     F(1), F("1.0208333333334"), NAND))
        gates.append(rel_gate([offset, clock],          True,      F(1), F("1.0208333333334"), NAND))
        gates.append(rel_gate([offset + 6, offset + 3], True,   F(".9"), F("1.0208333333334"), NAND))
        gates.append(rel_gate([offset + 2, data],       not value, F(1), F("1.0208333333334"), NAND))
        gates.append(rel_gate([offset + 1, offset + 5], value,     F(1), F("1.0208333333334"), NAND))
        gates.append(rel_gate([offset + 4, offset + 2], not value, F(1), F("1.0208333333334"), NAND))
        gates.append(rel_gate([offset + 1, clock],      False,  F(".1"), F(0), AND))  # fan-in for offset + 2
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
    gates.append(Gate([clock], False, F(10), F(0), F(0), NOT))
    gates.append(rel_gate([ffOutputQ, ffOutputR], False, F("1.0"), F("1.0208333333334"), OR))
    gates.append(rel_gate([ffOutputR],            False, F("0.5"), F("1.0208333333334"), COPY))
    gates.append(rel_gate([ffOutputP, ffOutputQ], False, F("1.5"), F("1.0208333333334"), XOR))
    create_flip_flop(gates, clock, gateP, True)
    create_flip_flop(gates, clock, gateQ, False)
    create_flip_flop(gates, clock, gateR, False)
    width = F(5)
    height = F(5)
    padding = F(1, 5)
    paths_to_display = [clock, ffOutputP, ffOutputQ, ffOutputR]
    path_names = ["clock", "P", "Q", "R"]
    end_time = F(240)
else:
    raise ValueError


runner = PathRunner(gates)
runner.truncate_at(end_time)

print("\\begin{tikzpicture}")

size = runner.get_size() if len(paths_to_display) == 0 else len(paths_to_display)
time = runner.get_time()

path_width = width - 2 * padding
path_height = (height - padding) / size - padding

for i in range(0, size):
    path_bottom = height - (padding + path_height) * (i + 1)
    path_middle = path_bottom + path_height / 2

    print("\\draw[very thin] (%f,%f) node[anchor=east]{%s} -- (%f,%f);"
            % (padding, path_middle, path_names[i],
               padding + path_width, path_middle))

    path = runner.get_path(i if len(paths_to_display) == 0
                           else paths_to_display[i])
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
