import numpy
import pyphi
from fractions import Fraction as F

# delta: tuple[tuple[str], tuple[str]] (1st is always one of ABX; 2nd is either one or both of remaining)
# env = tuple({"A", "B", "X", "I"} - set(delta[0]) - set(delta[1]))
# state = tuple[tuple[str, bool], ...]
# sigma: tuple[tuple[tuple[state], tuple[state]], tuple[tuple[state], tuple[state]]]
# epsilon: tuple[state] (where states include "I" plus possibly one other)

ABX = tuple("A", "B", "X")

def gen_delta():
    for i in range(3):
        first = ABX[i]
        for j in range(i + 1, 3):
            second = ABX[j]
            yield ((first,), (second,))
        rest = list(ABX)
        del rest[first]
        yield ((first,), tuple(rest))

def gen_epsilon(delta, prog):
    others = set(ABX) - set(delta[0]) - set(delta[1])
    assert len(others) == 0 or len(others) == 1
    other = list(others)[0] if others else None
    for I in prog.I_options:
        if not other:
            yield ((("I", I),),)
        else:
            yield ((("I", I), (other, 0)))
            yield ((("I", I), (other, 1)))
            yield ((("I", I), (other, 0)), (("I", I), (other, 1)))

def gen_sigma(delta):
    assert len(delta) == 2
    for sigma_sub_0 in gen_sigma_sub(delta[0]):
        for sigma_sub_1 in gen_sigma_sub(delta[1]):
            return (sigma_sub_0, sigma_sub_1)

def gen_sigma_sub(delta_sub):
    if len(delta_sub) == 1:
        v = delta_sub[0]
        yield ((((v, 0),),), (((v, 1),),))
        yield ((((v, 1),),), (((v, 0),),))
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
                            off.append(((v0, 0), (v1, 0)))
                        elif a == 1:
                            on.append(((v0, 0), (v1, 0)))

                        if b == 0:
                            off.append(((v0, 1), (v1, 0)))
                        elif b == 1:
                            on.append(((v0, 1), (v1, 0)))

                        if c == 0:
                            off.append(((v0, 0), (v1, 1)))
                        elif c == 1:
                            on.append(((v0, 0), (v1, 1)))

                        if d == 0:
                            off.append(((v0, 1), (v1, 1)))
                        elif d == 1:
                            on.append(((v0, 1), (v1, 1)))

                        if len(off) > 0 and len(in) > 0:
                            yield (tuple(off), tuple(on))

def calc_tpm(prog, delta, epsilon, sigma):
    tpm = []
    for macro_start in ((0, 0), (1, 0), (0, 1), (1, 1)):
        count = 0
        p0 = 0
        p1 = 0
        for ...:  # TODO: micro states of element 0
            for ...:  # TODO: micro states of element 1
                for ...:  # TODO: micro states of environment
                    count += 1
                    micro_start = ...  # TODO: combine from for loops
                    micro_end = do_prog(prog, micro_start)
                    macro_end = ...  # TODO: infer from micro_end
                    if macro_end[0]:
                        p0 += 1
                    if macro_end[1]:
                        p1 += 1
        tpm.append((F(p0, count), F(p1, count)))
    return tuple(tpm)

def calc_phi(tpm, state):
    TODO

def print_row(prog, tpm, phis):
    TODO

def lookup(state, reg):
    return [v for r, v in state if r == reg][0]

def do_prog(prog, state):
    A, B, X, I = prog(
        lookup(state, "X"),
        lookup(state, "Y"),
        lookup(state, "Z"),
        lookup(state, "I"),
    )
    return (("A", A), ("B", B), ("X", X), ("I", I))

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

for prog in (prog1, prog2):
    for delta in gen_delta():
        for epsilon in gen_epsilon(delta, prog):
            for sigma in gen_sigma(delta):
                tpm = calc_tpm(prog, delta, epsilon, sigma)
                phis = [calc_phi(tpm, state) for state in  ((0, 0), (1, 0), (0, 1), (1, 1))]
                print_row(prog, tpm, phis)
