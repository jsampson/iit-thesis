import operator

from fractions import Fraction as F
from functools import reduce

from gate import Gate, rel_gate
from path_runner import PathRunner


def OR(inputs):
    return any(inputs)

def COPY(inputs):
    assert len(inputs) == 1
    return inputs[0]

def XOR(inputs):
    return reduce(operator.xor, inputs, False)

# for idealized.tex
# p = Gate([1, 2], True,  F(1), F(0), F(0), OR)
# q = Gate([2],    False, F(1), F(0), F(0), COPY)
# r = Gate([0, 1], False, F(1), F(0), F(0), XOR)

# for jagged.tex
# p = rel_gate([1, 2], True,  F(1),     F("101/100"), OR)
# q = rel_gate([2],    False, F("1/2"), F("101/100"), COPY)
# r = rel_gate([0, 1], False, F("3/2"), F("101/100"), XOR)

# for flatline.tex
p = rel_gate([1, 2], True,  F(1),     F("10208333333334/10000000000000"), OR)
q = rel_gate([2],    False, F("1/2"), F("10208333333334/10000000000000"), COPY)
r = rel_gate([0, 1], False, F("3/2"), F("10208333333334/10000000000000"), XOR)

runner = PathRunner([p, q, r])

runner.truncate_at(F(40))

width = F(5)
height = F(4)
padding = F(1, 5)
paths_to_display = [0, 1, 2]
path_names = ["P", "Q", "R"]

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
