#!/usr/bin/env python3
#
# Justin's IIT Thesis - Causal Snapshotting Analyzer
# Copyright 2024 by Justin T. Sampson
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

import numpy
import pyphi
from enum import Enum
from fractions import Fraction as F
from itertools import chain, combinations
from typing import Generator, Iterable

class Reg(Enum):
    A = 0
    B = 1
    X = 2
    I = 3

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

Subdomain = set[Reg]
Substate = dict[Reg, int]
    
def gen_single_substates(self: Subdomain) -> Generator[list[Substate], None, None]:
    assert Reg.I not in self
    if len(self) == 0:
        yield [{}]
    else:
        assert len(self) == 1
        reg = list(self)[0]
        yield [{reg: 0}]
        yield [{reg: 1}]
        yield [{reg: 0}, {reg: 1}]

def combine_states(first: Substate, second: Substate) -> Substate:
    combined = first.copy()
    for r in second.keys():
        assert r not in combined
        combined[r] = second[r]
    return combined

def gen_delta() -> Generator[tuple[Subdomain, Subdomain], None, None]:
    yield ({Reg.A}, {Reg.B})
    yield ({Reg.A}, {Reg.X})
    yield ({Reg.A}, {Reg.B, Reg.X})
    yield ({Reg.B}, {Reg.A})
    yield ({Reg.B}, {Reg.X})
    yield ({Reg.B}, {Reg.A, Reg.X})
    yield ({Reg.X}, {Reg.A})
    yield ({Reg.X}, {Reg.B})
    yield ({Reg.X}, {Reg.A, Reg.B})
    yield ({Reg.A, Reg.B}, {Reg.X})
    yield ({Reg.A, Reg.X}, {Reg.B})
    yield ({Reg.B, Reg.X}, {Reg.A})

def state_product(
    left_states: list[Substate],
    right_states: list[Substate],
) -> list[Substate]:
    return [combine_states(l, r) for l in left_states for r in right_states]

def gen_epsilon(
    delta: tuple[Subdomain, Subdomain],
    I_options: Iterable[int],
) -> Generator[list[Substate], None, None]:
    others = {Reg.A, Reg.B, Reg.X} - delta[0] - delta[1]
    for Is in chain.from_iterable(
        combinations(I_options, r) for r in range(1, len(I_options) + 1)
    ):
        I_parts = [{Reg.I: I} for I in Is]
        for other_parts in gen_single_substates(others):
            yield state_product(other_parts, I_parts)

def gen_sigma(delta: tuple[Subdomain, Subdomain]) -> Generator[
    tuple[
        tuple[list[Substate], list[Substate]],
        tuple[list[Substate], list[Substate]],
    ],
    None,
    None,
]:
    for sigma_sub_0 in gen_sigma_sub(delta[0]):
        for sigma_sub_1 in gen_sigma_sub(delta[1]):
            yield (sigma_sub_0, sigma_sub_1)

def gen_sigma_sub(delta_sub: Subdomain) -> Generator[
    tuple[list[Substate], list[Substate]], None, None
]:
    if len(delta_sub) == 1:
        v, = delta_sub
        yield ([{v: 0}], [{v: 1}])
        yield ([{v: 1}], [{v: 0}])
    else:
        assert len(delta_sub) == 2
        v0, v1 = delta_sub
        for a in range(3):
            for b in range(3):
                for c in range(3):
                    for d in range(3):
                        off = []
                        on = []

                        if a == 0:
                            off.append({v0: 0, v1: 0})
                        elif a == 1:
                            on.append({v0: 0, v1: 0})

                        if b == 0:
                            off.append({v0: 1, v1: 0})
                        elif b == 1:
                            on.append({v0: 1, v1: 0})

                        if c == 0:
                            off.append({v0: 0, v1: 1})
                        elif c == 1:
                            on.append({v0: 0, v1: 1})

                        if d == 0:
                            off.append({v0: 1, v1: 1})
                        elif d == 1:
                            on.append({v0: 1, v1: 1})

                        if len(off) > 0 and len(on) > 0:
                            yield (off, on)

def calc_tpm(prog, epsilon: list[Substate], sigma: tuple[
    tuple[list[Substate], list[Substate]],
    tuple[list[Substate], list[Substate]],
]) -> tuple[tuple[F, ...], ...]:
    tpm = []
    for macro_start in ((0, 0), (1, 0), (0, 1), (1, 1)):
        count = 0
        p0 = 0
        p1 = 0
        for elem_0_micro in sigma[0][macro_start[0]]:
            for elem_1_micro in sigma[1][macro_start[1]]:
                for env_micro in epsilon:
                    count += 1
                    micro_start = combine_states(combine_states(elem_0_micro, elem_1_micro), env_micro)
                    micro_end = do_prog(prog, micro_start)
                    macro_end = (F(1, 2), F(1, 2))
                    for _step in range(100):
                        if restriction_satisfies(micro_end, epsilon):
                            macro_end = (
                                macro_bit(sigma, micro_end, 0),
                                macro_bit(sigma, micro_end, 1),
                            )
                            break
                        else:
                            micro_end = do_prog(prog, micro_end)
                    p0 += macro_end[0]
                    p1 += macro_end[1]
        tpm.append((F(p0, count), F(p1, count)))
    return tuple(tpm)

def restriction_satisfies(micro_state: Substate, valid_states: list[Substate]):
    if not valid_states:
        return False
    else:
        example = valid_states[0]
        restricted_state = {}
        for reg in example.keys():
            restricted_state[reg] = micro_state[reg]
        return restricted_state in valid_states

def macro_bit(sigma: tuple[
    tuple[list[Substate], list[Substate]],
    tuple[list[Substate], list[Substate]],
], micro_state: Substate, i: int):
    if restriction_satisfies(micro_state, sigma[i][0]):
        return F(0)
    elif restriction_satisfies(micro_state, sigma[i][1]):
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

    phis = []
    for state in ((0, 0), (1, 0), (0, 1), (1, 1)):
        try:
            phi = round(pyphi.compute.phi(pyphi.Subsystem(network, state)), 4)
        except pyphi.exceptions.StateUnreachableError:
            phi = -1
        phis.append(phi)
    phis = tuple(phis)
    tpm_to_phis[tpm] = phis
    return phis

def do_prog(prog, state):
    A, B, X, I = prog(state[Reg.A], state[Reg.B], state[Reg.X], state[Reg.I])
    return {Reg.A: A, Reg.B: B, Reg.X: X, Reg.I: I}

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

prog1.display_name = "Original"
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

prog2.display_name = "Decomposed"
prog2.I_options = (4, 5)

def main():
    for prog in (prog1, prog2):
        tpms = {}
        phis = {}
        full = {}
        for delta in gen_delta():
            for epsilon in gen_epsilon(delta, prog.I_options):
                for sigma in gen_sigma(delta):
                    tpm = calc_tpm(prog, epsilon, sigma)
                    if tpm in tpms:
                        tpm_phis = tpms[tpm]
                    else:
                        tpm_phis = calc_phis(tpm)
                        tpms[tpm] = tpm_phis
                    sorted_phis = tuple(sorted(tpm_phis, reverse=True))
                    if sorted_phis in phis:
                        phis[sorted_phis].add(tpm)
                    else:
                        phis[sorted_phis] = {tpm}
                    full_info = (prog, delta, epsilon, sigma, tpm, tpm_phis)
                    if sorted_phis in full:
                        full[sorted_phis].append(full_info)
                    else:
                        full[sorted_phis] = [full_info]
        prog.tpms = tpms
        prog.phis = phis
        print(prog.display_name, ":", len(tpms), "TPMs")
        for sorted_phi in sorted(phis.keys(), reverse=True):
            print(sorted_phi, "Phi values in", len(phis[sorted_phi]), "TPMs")
        highest_phi = sorted(phis.keys(), reverse=True)[0]
        print("All snapshot specifications with highest Phi:")
        for _prog, delta, epsilon, sigma, tpm, tpm_phis in full[highest_phi]:
            print("- delta:  ", delta)
            print("  epsilon:", epsilon)
            print("  sigma:  ", sigma)
            print("  TPM:    ", " | ".join(" ".join(str(cell) for cell in row) for row in tpm))
            print("  Phi:    ", tpm_phis)
    print("Common TPMs:")
    common_count = 0
    for tpm in prog1.tpms:
        if tpm in prog2.tpms:
            common_count += 1
            tpm_phis = prog1.tpms[tpm]
            print(" | ".join(" ".join(str(cell) for cell in row) for row in tpm), "=>", tpm_phis)
    print(common_count, "TPMs in common")

if __name__ == "__main__":
    main()