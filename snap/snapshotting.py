#!/usr/bin/env python3
#
# Code to accompany Causal Snapshotting paper
# Copyright 2025 by Justin T. Sampson
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


from math import prod


def print_mat(mat: list[list[float]]) -> None:
    h = len(mat)
    w = len(mat[0])
    assert all(len(row) == w for row in mat)

    hb = h.bit_length() - 1
    assert h == (1 << hb)
    assert 1 <= hb <= 6

    wb = w.bit_length() - 1
    assert w == (1 << wb)
    assert 1 <= wb <= 6

    print(" " * (hb + 1) + " ".join(" " * (6 - wb) + bin(i)[2:].zfill(wb) for i in range(w)))
    for j in range(len(mat)):
        row = mat[j]
        print(bin(j)[2:].zfill(hb) + " " + " ".join(f"{cell:.4f}" for cell in row))

def eq_approx(a: float,  b: float) -> bool:
    return -0.000000001 <= (a - b) <= +0.000000001

def in_range(a: float) -> bool:
    return -0.000000001 <= a <= +1.000000001

def is_valid_dist(mat: list[float]) -> bool:
    return eq_approx(1, sum(mat)) and all(in_range(val) for val in mat)

def is_valid_joint(mat: list[list[float]]) -> bool:
    return eq_approx(1, sum(sum(row) for row in mat)) and all(
        all(in_range(val) for val in row) for row in mat
    )

def is_valid_cond(mat: list[list[float]]) -> bool:
    return all(
        is_valid_dist([row[i] for row in mat])
        for i in range(len(mat[0]))
    )


Omega_U = range(2 ** 6)

PU_next_u_if_prev_u = [[0.0 for prev_u in Omega_U] for next_u in Omega_U]
for prev_u in Omega_U:
    next_u = ((prev_u & 0b101010) >> 1) & (prev_u & 0b010101)
    next_u = (next_u >> 1) | (next_u >> 2) | (next_u << 4) | (next_u << 5)
    next_u = next_u & 0b111111
    PU_next_u_if_prev_u[next_u][prev_u] = 1.0

assert is_valid_cond(PU_next_u_if_prev_u)


Omega_S = range(2 ** 3)
Omega_ui = range(2 ** 2)
Omega_si = range(2)

def u_i(u, i):
    assert 1 <= i <= 3
    return (u >> (2 * (3 - i))) & 0b11

def s_i(s, i):
    assert 1 <= i <= 3
    return (s >> (3 - i)) & 0b1


# PS_si_if_ui = [
#     [1, 1, 1, 0],
#     [0, 0, 0, 1],
# ]
PS_si_if_ui = [
    [.95, .9, .9, .15],
    [.05, .1, .1, .85],
]

assert is_valid_cond(PS_si_if_ui)


PS_ui = [
    1.0 / len(Omega_ui)
    for ui in Omega_ui
]

assert is_valid_dist(PS_ui)


PS_ui_and_si = [[PS_si_if_ui[si][ui] * PS_ui[ui] for si in Omega_si] for ui in Omega_ui]

assert is_valid_joint(PS_ui_and_si)


PS_si = [
    sum(PS_ui_and_si[ui][si] for ui in Omega_ui)
    for si in Omega_si
]

assert is_valid_dist(PS_si)


PS_ui_if_si = [
    [
        PS_ui_and_si[ui][si] / PS_si[si]
        for si in Omega_si
    ]
    for ui in Omega_ui
]

assert is_valid_cond(PS_ui_if_si)


PS_u_if_s = [
    [
        prod(PS_ui_if_si[u_i(u, i)][s_i(s, i)] for i in (1, 2, 3))
        for s in Omega_S
    ]
    for u in Omega_U
]

assert is_valid_cond(PS_u_if_s)


PS_next_si_if_s = {i: [[0.0 for s in Omega_S] for next_si in (0, 1)] for i in (1, 2, 3)}
for i in (1, 2, 3):
    for next_si in (0, 1):
        for s in Omega_S:
            for u in Omega_U:
                for next_u in Omega_U:
                    PS_next_si_if_s[i][next_si][s] += \
                        PS_u_if_s[u][s] \
                        * PU_next_u_if_prev_u[next_u][u] \
                        * PS_si_if_ui[next_si][u_i(next_u, i)]

for i in (1, 2, 3):
    assert is_valid_cond(PS_next_si_if_s[i])


PS_next_s_if_s = [
    [
        prod(PS_next_si_if_s[i][s_i(next_s, i)][s] for i in (1, 2, 3))
        for s in Omega_S
    ]
    for next_s in Omega_S
]

assert is_valid_cond(PS_next_s_if_s)


for i in (1, 2, 3):
    for next_si in (0, 1):
        for s in Omega_S:
            assert eq_approx(
                PS_next_si_if_s[i][next_si][s],
                sum(
                    PS_next_s_if_s[next_s][s]
                    for next_s in Omega_S
                    if s_i(next_s, i) == next_si
                )
            )


print_mat(PS_next_s_if_s)


def print_tpm(tpm: dict[int, list[list[float]]]) -> None:
    b = len(tpm)
    assert 1 <= b <= 6
    assert tpm.keys() == set(range(1, b + 1))

    h = len(tpm[1])
    w = len(tpm[1][0])
    assert all(
        len(mat) == h
        and all(len(row) == w for row in mat)
        for mat in tpm.values()
    )

    hb = h.bit_length() - 1
    assert h == (1 << hb)
    assert hb == 1

    wb = w.bit_length() - 1
    assert w == (1 << wb)
    assert wb == b

    for s in range(1 << b):
        le = 0
        for i in range(b):
            le <<= 1
            le |= ((s >> i) & 1)
        le_bin = bin(le)[2:].zfill(b)
        line = " & ".join(le_bin)
        for i in range(1, b + 1):
            off = tpm[i][0][le]
            on = tpm[i][1][le]
            assert eq_approx(1, off + on)
            line += f" & {on:.4f}"
        line += r" \\"
        print(line)


print()
print_tpm(PS_next_si_if_s)


# PS_si_if_ui = [
#     [1, 1, 1, 0],
#     [0, 0, 0, 1],
# ]
#
#        000    001    010    011    100    101    110    111
# 000 1.0000 0.0000 0.0000 0.0000 0.0000 0.0000 0.0000 0.0000
# 001 0.0000 0.0000 1.0000 0.0000 0.0000 0.0000 0.0000 0.0000
# 010 0.0000 0.0000 0.0000 0.0000 1.0000 0.0000 0.0000 0.0000
# 011 0.0000 0.0000 0.0000 0.0000 0.0000 0.0000 1.0000 0.0000
# 100 0.0000 1.0000 0.0000 0.0000 0.0000 0.0000 0.0000 0.0000
# 101 0.0000 0.0000 0.0000 1.0000 0.0000 0.0000 0.0000 0.0000
# 110 0.0000 0.0000 0.0000 0.0000 0.0000 1.0000 0.0000 0.0000
# 111 0.0000 0.0000 0.0000 0.0000 0.0000 0.0000 0.0000 1.0000
#
# 0 & 0 & 0 & 0.0000 & 0.0000 & 0.0000 \\
# 1 & 0 & 0 & 0.0000 & 1.0000 & 0.0000 \\
# 0 & 1 & 0 & 0.0000 & 0.0000 & 1.0000 \\
# 1 & 1 & 0 & 0.0000 & 1.0000 & 1.0000 \\
# 0 & 0 & 1 & 1.0000 & 0.0000 & 0.0000 \\
# 1 & 0 & 1 & 1.0000 & 1.0000 & 0.0000 \\
# 0 & 1 & 1 & 1.0000 & 0.0000 & 1.0000 \\
# 1 & 1 & 1 & 1.0000 & 1.0000 & 1.0000 \\

# PS_si_if_ui = [
#     [.95, .9, .9, .15],
#     [.05, .1, .1, .85],
# ]
#
#        000    001    010    011    100    101    110    111
# 000 0.7501 0.2739 0.2739 0.1000 0.2739 0.1000 0.1000 0.0365
# 001 0.0754 0.0276 0.5516 0.2015 0.0276 0.0101 0.2015 0.0736
# 010 0.0754 0.0276 0.0276 0.0101 0.5516 0.2015 0.2015 0.0736
# 011 0.0076 0.0028 0.0555 0.0203 0.0555 0.0203 0.4057 0.1481
# 100 0.0754 0.5516 0.0276 0.2015 0.0276 0.2015 0.0101 0.0736
# 101 0.0076 0.0555 0.0555 0.4057 0.0028 0.0203 0.0203 0.1481
# 110 0.0076 0.0555 0.0028 0.0203 0.0555 0.4057 0.0203 0.1481
# 111 0.0008 0.0056 0.0056 0.0408 0.0056 0.0408 0.0408 0.2983
#
# 0 & 0 & 0 & 0.0914 & 0.0914 & 0.0914 \\
# 1 & 0 & 0 & 0.0914 & 0.6682 & 0.0914 \\
# 0 & 1 & 0 & 0.0914 & 0.0914 & 0.6682 \\
# 1 & 1 & 0 & 0.0914 & 0.6682 & 0.6682 \\
# 0 & 0 & 1 & 0.6682 & 0.0914 & 0.0914 \\
# 1 & 0 & 1 & 0.6682 & 0.6682 & 0.0914 \\
# 0 & 1 & 1 & 0.6682 & 0.0914 & 0.6682 \\
# 1 & 1 & 1 & 0.6682 & 0.6682 & 0.6682 \\

# TODO: factor out most of above to function from PS_si_if_ui and PU_next_u_if_prev_u to PS_next_s_if_s
# TODO: generalize so this can work with cascade decomposition example
