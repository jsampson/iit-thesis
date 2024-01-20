import numpy
import pyphi
from fractions import Fraction as F

def gen_delta():
    yield ("B", "AX")  # TODO: remove
    yield ("A", "B")
    yield ("A", "X")
    yield ("A", "BX")
    yield ("B", "A")
    yield ("B", "X")
    yield ("B", "AX")
    yield ("X", "A")
    yield ("X", "B")
    yield ("X", "AB")
    yield ("AB", "X")
    yield ("AX", "B")
    yield ("BX", "A")

def gen_epsilon(delta, prog):
    others = set("ABX") - set(delta[0]) - set(delta[1])
    assert len(others) == 0 or len(others) == 1
    other = list(others)[0] if others else None
    for I in prog.I_options:
        if not other:
            yield (f"I{I}",)
        else:
            yield (f"{other}0I{I}", f"{other}1I{I}") # TODO: move back to last
            yield (f"{other}0I{I}",)
            yield (f"{other}1I{I}",)

def gen_sigma(delta):
    assert len(delta) == 2
    for sigma_sub_0 in gen_sigma_sub(delta[0]):
        for sigma_sub_1 in gen_sigma_sub(delta[1]):
            yield (sigma_sub_0, sigma_sub_1)

def gen_sigma_sub(delta_sub):
    if len(delta_sub) == 1:
        v = delta_sub[0]
        yield ((f"{v}0",), (f"{v}1",))
        yield ((f"{v}1",), (f"{v}0",))
    else:
        assert len(delta_sub) == 2
        v0 = delta_sub[0]
        v1 = delta_sub[1]
        for a in range(3):
            for b in range(3):
                for c in range(3):
                    for d in range(3):
                        off = []
                        on = []

                        if a == 0:
                            off.append(f"{v0}0{v1}0")
                        elif a == 1:
                            on.append(f"{v0}0{v1}0")

                        if b == 0:
                            off.append(f"{v0}1{v1}0")
                        elif b == 1:
                            on.append(f"{v0}1{v1}0")

                        if c == 0:
                            off.append(f"{v0}0{v1}1")
                        elif c == 1:
                            on.append(f"{v0}0{v1}1")

                        if d == 0:
                            off.append(f"{v0}1{v1}1")
                        elif d == 1:
                            on.append(f"{v0}1{v1}1")

                        if len(off) > 0 and len(on) > 0:
                            yield (tuple(off), tuple(on))

def calc_tpm(prog, delta, epsilon, sigma):
    tpm = []
    for macro_start in ((0, 0), (1, 0), (0, 1), (1, 1)):
        count = 0
        p0 = 0
        p1 = 0
        for elem_0_micro in sigma[0][macro_start[0]]:
            for elem_1_micro in sigma[1][macro_start[1]]:
                for env_micro in epsilon:
                    count += 1
                    micro_start = elem_0_micro + elem_1_micro + env_micro
                    micro_end = do_prog(prog, micro_start)
                    macro_end = (
                        macro_bit(delta, sigma, micro_end, 0),
                        macro_bit(delta, sigma, micro_end, 1),
                    )
                    p0 += macro_end[0]
                    p1 += macro_end[1]
        tpm.append((F(p0, count), F(p1, count)))
    return tuple(tpm)

def macro_bit(delta, sigma, micro_state, i):
    restricted_state = ""
    for v in delta[i]:
        restricted_state += f"{v}{lookup(micro_state, v)}"
    if restricted_state in sigma[i][0]:
        return F(0)
    elif restricted_state in sigma[i][1]:
        return F(1)
    else:
        return F("1/2")

tpm_to_network = {}
tpm_to_phis = {}

def calc_phis(tpm):
    if tpm in tpm_to_phis:
        return tpm_to_phis[tpm]

    if tpm in tpm_to_network:
        network = tpm_to_network[tpm]
    else:
        network = pyphi.Network(numpy.array([
            [float(cell) for cell in row]
            for row in tpm
        ]))
        tpm_to_network[tpm] = network

    phis = tuple(
        pyphi.compute.phi(pyphi.Subsystem(network, state))
        for state in ((0, 0), (1, 0), (0, 1), (1, 1))
    )
    tpm_to_phis[tpm] = phis
    return phis

def print_row(prog, tpm, phis):
    # TODO: turn into LaTeX
    print(prog)
    print("; ".join((", ".join((str(f) for f in r)) for r in tpm)))
    print(phis)

def lookup(state, reg):
    assert reg in state
    reg_index = state.index(reg)
    return int(state[reg_index + 1])

def do_prog(prog, state):
    A, B, X, I = prog(
        lookup(state, "A"),
        lookup(state, "B"),
        lookup(state, "X"),
        lookup(state, "I"),
    )
    return f"A{A}B{B}X{X}I{I}"

def prog1(A, B, X, I):
    if I == 3:
        X = A
        A = B
        B = X
    elif I == 4:
        A = B
        B = X
        X = A
    else:
        assert I == 5
        B = X
        X = A
        A = B
    return A, B, X, I

prog1.I_options = (3, 4, 5)

def prog2(A, B, X, I):
    if I == 4:
        A = B
        B = B ^ X
    else:
        assert I == 5
        B = B ^ X
        A = B
    return A, B, X, I

prog2.I_options = (4, 5)

def main(limit = 1, progs = (prog1, prog2)):
    count = 0
    for prog in progs:
        for delta in gen_delta():
            for epsilon in gen_epsilon(delta, prog):
                for sigma in gen_sigma(delta):
                    tpm = calc_tpm(prog, delta, epsilon, sigma)
                    phis = calc_phis(tpm)
                    print_row(prog, tpm, phis)
                    count += 1
                    if count >= limit:
                        return

# TODO: compare complete set of TPMs; is there any overlap between the two programs?
# TODO: compare range of phi values as well, but round for comparison
# TODO: display statistics, e.g.
# - number of distinct TPMs per program
# - number of TPMs with each unordered combination of phi values
# - can do this with a map from phis to sets of tpms