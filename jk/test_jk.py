# Justin's IIT Thesis - J-K flip-flop simulator
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

import re
import unittest
from jk import *

class JKTests(unittest.TestCase):
    def test_combine(self):
        self.assertEqual(
            combine(
                [
                    "a1b2",
                    "a3b5",
                ],
                [
                    "c5d6",
                    "c7d8",
                ],
            ),
            [
                    "a1b2c5d6",
                    "a1b2c7d8",
                    "a3b5c5d6",
                    "a3b5c7d8",
            ],
        )

    def test_all_states_for(self):
        self.assertEqual(
            all_states_for(iter(["a", "b", "c"])),
            [
                "a.b.c.",
                "a.b.c*",
                "a.b*c.",
                "a.b*c*",
                "a*b.c.",
                "a*b.c*",
                "a*b*c.",
                "a*b*c*",
            ],
        )

    def test_all_starting_states(self):
        states = all_starting_states()
        self.assertEqual(len(states), 2048)
        self.assertEqual(states[0], "S.R*C*J.K.1.2.3.4.5.6.Q.N.")
        self.assertEqual(states[2047], "S*R.C*J*K*1*2*3*4*5*6*Q*N*")

    def test_stable_starting_states(self):
        self.assertEqual(
            stable_starting_states(),
            """
            S.R*C*J.K.1*2.3*4*5.6.Q*N.
            S.R*C*J.K*1*2.3*4.5.6*Q*N.
            S.R*C*J*K.1*2.3*4*5.6.Q*N.
            S.R*C*J*K*1*2.3*4.5.6*Q*N.
            S*R.C*J.K.1.2*3.4*5.6.Q.N*
            S*R.C*J.K*1.2*3.4*5.6.Q.N*
            S*R.C*J*K.1.2*3.4*5.6.Q.N*
            S*R.C*J*K*1.2*3.4*5.6.Q.N*
            """.split(),
        )

    def test_stable_post_boot_states(self):
        self.assertEqual(
            stable_post_boot_states(),
            """
            S*R*C*J.K.1*2.3*4*5.6.Q*N.
            S*R*C*J.K*1*2.3*4.5.6*Q*N.
            S*R*C*J*K.1*2.3*4*5.6.Q*N.
            S*R*C*J*K*1*2.3*4.5.6*Q*N.
            S*R*C*J.K.1.2*3.4*5.6.Q.N*
            S*R*C*J.K*1.2*3.4*5.6.Q.N*
            S*R*C*J*K.1.2*3.4*5.6.Q.N*
            S*R*C*J*K*1.2*3.4*5.6.Q.N*
            """.split(),
        )

    def test_stable_clock_down_after_start_states(self):
        self.assertEqual(
            stable_clock_down_after_start_states(),
            """
            S*R*C.J.K.1.2*3*4*5.6.Q*N.
            S*R*C.J.K*1*2*3*4.5.6*Q*N.
            S*R*C.J*K.1.2*3*4*5.6.Q*N.
            S*R*C.J*K*1*2*3*4.5.6*Q*N.
            S*R*C.J.K.1.2*3*4*5.6.Q.N*
            S*R*C.J.K*1.2*3*4*5.6.Q.N*
            S*R*C.J*K.1*2*3*4.5*6.Q.N*
            S*R*C.J*K*1*2*3*4.5*6.Q.N*
            """.split(),
        )

    def test_stable_clock_up_states(self):
        self.assertEqual(
            stable_clock_up_states(),
            """
            S*R*C*J.K.1.2*3.4*5.6.Q.N*
            S*R*C*J.K*1*2.3*4.5.6*Q*N.
            S*R*C*J*K.1.2*3.4*5.6.Q.N*
            S*R*C*J*K*1*2.3*4.5.6*Q*N.
            S*R*C*J.K.1.2*3.4*5.6.Q.N*
            S*R*C*J.K*1.2*3.4*5.6.Q.N*
            S*R*C*J*K.1*2.3*4*5.6.Q*N.
            S*R*C*J*K*1*2.3*4.5.6*Q*N.
            """.split(),
        )

    def test_perturbation_of_456(self):
        count_of_states_checked = 0
        for state in stable_post_boot_states() + stable_clock_up_states():
            if state[-1] == ".":
                perturbed = re.sub("4(.)5(.)6(.)", r"4\g<3>5\g<2>6\g<1>", state)
                stable = stabilize(perturbed, jk)
                self.assertEqual(stable, state)
                count_of_states_checked += 1
            else:
                self.assertTrue("4*5.6." in state)
        self.assertEqual(count_of_states_checked, 8)
