# Justin's IIT Thesis - Digital Circuit Simulator
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

import operator
import unittest

from fractions import Fraction as F
from functools import reduce

from gate import Gate
from path_runner import PathRunner


def COPY(inputs):
    assert len(inputs) == 1
    return inputs[0]

def NOR(inputs):
    return not any(inputs)

def NOT(inputs):
    assert len(inputs) == 1
    return not inputs[0]

def OR(inputs):
    return any(inputs)

def XOR(inputs):
    return reduce(operator.xor, inputs, False)


class PathRunnerTestCase(unittest.TestCase):

    def setUp(self):
        p = Gate([1, 2], True, (1.5, 1, 1), OR)
        q = Gate([2], False, (.5, 1, 1), COPY)
        r = Gate([0, 1], False, (2.5, 1, 1), XOR)
        self.runner = PathRunner([p, q, r])

    def test_step0(self):
        self.doSteps(0)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0)
        self.assertPath(1, 0.0, 0.0, 0.5, 0.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0)
        self.assertTime(0.5)

    def test_step1(self):
        self.doSteps(1)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0)
        self.assertPath(1, 0.0, 0.0, 3.0, 0.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0)
        self.assertTime(1.5)

    def test_step2(self):
        self.doSteps(2)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 4.0, 0.0)
        self.assertPath(1, 0.0, 0.0, 3.0, 0.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0)
        self.assertTime(2.5)

    def test_step3(self):
        self.doSteps(3)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 4.0, 0.0)
        self.assertPath(1, 0.0, 0.0, 3.0, 0.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.5, 1.0, 4.5, 1.0)
        self.assertTime(3.0)

    def test_step4(self):
        self.doSteps(4)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 4.0, 0.0)
        self.assertPath(1, 0.0, 0.0, 3.5, 0.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.5, 1.0, 4.5, 1.0)
        self.assertTime(3.5)

    def test_step5(self):
        self.doSteps(5)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 4.0, 0.0)
        self.assertPath(1, 0.0, 0.0, 3.5, 0.0, 4.5, 1.0, 5.0, 1.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.5, 1.0, 4.5, 1.0)
        self.assertTime(4.0)

    def test_step6(self):
        self.doSteps(6)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 4.5, 0.0)
        self.assertPath(1, 0.0, 0.0, 3.5, 0.0, 4.5, 1.0, 5.0, 1.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.5, 1.0, 4.5, 1.0)
        self.assertTime(4.5)

    def test_step7(self):
        self.doSteps(7)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 4.5, 0.0, 5.5, 1.0)
        self.assertPath(1, 0.0, 0.0, 3.5, 0.0, 4.5, 1.0, 5.0, 1.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.5, 1.0, 4.5, 1.0, 5.5, 0.0, 6.5, 0.0)
        self.assertTime(5.0)

    def test_step8(self):
        self.doSteps(8)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 4.5, 0.0, 5.5, 1.0)
        self.assertPath(1, 0.0, 0.0, 3.5, 0.0, 4.5, 1.0, 5.5, 1.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.5, 1.0, 4.5, 1.0, 5.5, 0.0, 6.5, 0.0)
        self.assertTime(5.5)

    def test_step9(self):
        self.doSteps(9)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 4.5, 0.0, 5.5, 1.0, 6.5, 1.0)
        self.assertPath(1, 0.0, 0.0, 3.5, 0.0, 4.5, 1.0, 5.5, 1.0, 6.5, 0.0, 7.0, 0.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.5, 1.0, 4.5, 1.0, 5.5, 0.0, 6.5, 0.0)
        self.assertTime(6.5)

    def test_step10(self):
        self.doSteps(10)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 4.5, 0.0, 5.5, 1.0, 7.5, 1.0)
        self.assertPath(1, 0.0, 0.0, 3.5, 0.0, 4.5, 1.0, 5.5, 1.0, 6.5, 0.0, 7.0, 0.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.5, 1.0, 4.5, 1.0, 5.5, 0.0, 6.5, 0.0, 7.5, 1.0)
        self.assertTime(7.0)

    def test_step11(self):
        self.doSteps(11)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 4.5, 0.0, 5.5, 1.0, 7.5, 1.0)
        self.assertPath(1, 0.0, 0.0, 3.5, 0.0, 4.5, 1.0, 5.5, 1.0, 6.5, 0.0, 7.5, 0.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.5, 1.0, 4.5, 1.0, 5.5, 0.0, 6.5, 0.0, 7.5, 1.0)
        self.assertTime(7.5)

    def test_step12(self):
        self.doSteps(12)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 4.5, 0.0, 5.5, 1.0, 7.5, 1.0, 8.5, 0.0)
        self.assertPath(1, 0.0, 0.0, 3.5, 0.0, 4.5, 1.0, 5.5, 1.0, 6.5, 0.0, 7.5, 0.0, 8.0, 0.5)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.5, 1.0, 4.5, 1.0, 5.5, 0.0, 6.5, 0.0, 7.5, 1.0, 8.5, 0.0)
        self.assertTime(8.0)

    def test_step13(self):
        self.doSteps(13)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 4.5, 0.0, 5.5, 1.0, 7.5, 1.0, 8.5, 0.0)
        self.assertPath(1, 0.0, 0.0, 3.5, 0.0, 4.5, 1.0, 5.5, 1.0, 6.5, 0.0, 7.5, 0.0, 8.5, 1.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.5, 1.0, 4.5, 1.0, 5.5, 0.0, 6.5, 0.0, 7.5, 1.0, 8.5, 0.0)
        self.assertTime(8.5)

    def test_step14(self):
        self.doSteps(14)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 4.5, 0.0, 5.5, 1.0, 7.5, 1.0, 8.5, 0.0, 9.5, 1.0)
        self.assertPath(1, 0.0, 0.0, 3.5, 0.0, 4.5, 1.0, 5.5, 1.0, 6.5, 0.0, 7.5, 0.0, 8.5, 1.0, 9.0, 0.5)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.5, 1.0, 4.5, 1.0, 5.5, 0.0, 6.5, 0.0, 7.5, 1.0, 8.5, 0.0, 9.5, 1.0, 10.5, 1.0)
        self.assertTime(9.0)

    def test_step15(self):
        self.doSteps(15)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 4.5, 0.0, 5.5, 1.0, 7.5, 1.0, 8.5, 0.0, 9.5, 1.0)
        self.assertPath(1, 0.0, 0.0, 3.5, 0.0, 4.5, 1.0, 5.5, 1.0, 6.5, 0.0, 7.5, 0.0, 8.5, 1.0, 9.5, 0.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.5, 1.0, 4.5, 1.0, 5.5, 0.0, 6.5, 0.0, 7.5, 1.0, 8.5, 0.0, 9.5, 1.0, 10.5, 1.0)
        self.assertTime(9.5)

    def test_step16(self):
        self.doSteps(16)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 4.5, 0.0, 5.5, 1.0, 7.5, 1.0, 8.5, 0.0, 9.5, 1.0, 10.5, 1.0)
        self.assertPath(1, 0.0, 0.0, 3.5, 0.0, 4.5, 1.0, 5.5, 1.0, 6.5, 0.0, 7.5, 0.0, 8.5, 1.0, 9.5, 0.0, 10.5, 1.0, 11.0, 1.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.5, 1.0, 4.5, 1.0, 5.5, 0.0, 6.5, 0.0, 7.5, 1.0, 8.5, 0.0, 9.5, 1.0, 10.5, 1.0)
        self.assertTime(10.5)

    def test_step17(self):
        self.doSteps(17)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 4.5, 0.0, 5.5, 1.0, 7.5, 1.0, 8.5, 0.0, 9.5, 1.0, 11.5, 1.0)
        self.assertPath(1, 0.0, 0.0, 3.5, 0.0, 4.5, 1.0, 5.5, 1.0, 6.5, 0.0, 7.5, 0.0, 8.5, 1.0, 9.5, 0.0, 10.5, 1.0, 11.0, 1.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.5, 1.0, 4.5, 1.0, 5.5, 0.0, 6.5, 0.0, 7.5, 1.0, 8.5, 0.0, 9.5, 1.0, 11.5, 1.0)
        self.assertTime(11.0)

    def test_step18(self):
        self.doSteps(18)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 4.5, 0.0, 5.5, 1.0, 7.5, 1.0, 8.5, 0.0, 9.5, 1.0, 11.5, 1.0)
        self.assertPath(1, 0.0, 0.0, 3.5, 0.0, 4.5, 1.0, 5.5, 1.0, 6.5, 0.0, 7.5, 0.0, 8.5, 1.0, 9.5, 0.0, 10.5, 1.0, 12.0, 1.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.5, 1.0, 4.5, 1.0, 5.5, 0.0, 6.5, 0.0, 7.5, 1.0, 8.5, 0.0, 9.5, 1.0, 11.5, 1.0)
        self.assertTime(11.5)

    def test_step19(self):
        self.doSteps(19)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 4.5, 0.0, 5.5, 1.0, 7.5, 1.0, 8.5, 0.0, 9.5, 1.0, 13.0, 1.0)
        self.assertPath(1, 0.0, 0.0, 3.5, 0.0, 4.5, 1.0, 5.5, 1.0, 6.5, 0.0, 7.5, 0.0, 8.5, 1.0, 9.5, 0.0, 10.5, 1.0, 12.0, 1.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.5, 1.0, 4.5, 1.0, 5.5, 0.0, 6.5, 0.0, 7.5, 1.0, 8.5, 0.0, 9.5, 1.0, 12.5, 1.0)
        self.assertTime(12.0)

    def test_step20(self):
        self.doSteps(20)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 4.5, 0.0, 5.5, 1.0, 7.5, 1.0, 8.5, 0.0, 9.5, 1.0, 13.0, 1.0)
        self.assertPath(1, 0.0, 0.0, 3.5, 0.0, 4.5, 1.0, 5.5, 1.0, 6.5, 0.0, 7.5, 0.0, 8.5, 1.0, 9.5, 0.0, 10.5, 1.0, 13.0, 1.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.5, 1.0, 4.5, 1.0, 5.5, 0.0, 6.5, 0.0, 7.5, 1.0, 8.5, 0.0, 9.5, 1.0, 12.5, 1.0)
        self.assertTime(12.5)

    def test_step21(self):
        self.doSteps(21)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 4.5, 0.0, 5.5, 1.0, 7.5, 1.0, 8.5, 0.0, 9.5, 1.0, 13.0, 1.0)
        self.assertPath(1, 0.0, 0.0, 3.5, 0.0, 4.5, 1.0, 5.5, 1.0, 6.5, 0.0, 7.5, 0.0, 8.5, 1.0, 9.5, 0.0, 10.5, 1.0, 13.0, 1.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.5, 1.0, 4.5, 1.0, 5.5, 0.0, 6.5, 0.0, 7.5, 1.0, 8.5, 0.0, 9.5, 1.0, 12.5, 1.0, 13.5, 0.0, 15.5, 0.0)
        self.assertTime(13.0)

    def test_step22(self):
        self.doSteps(22)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 4.5, 0.0, 5.5, 1.0, 7.5, 1.0, 8.5, 0.0, 9.5, 1.0, 14.5, 1.0)
        self.assertPath(1, 0.0, 0.0, 3.5, 0.0, 4.5, 1.0, 5.5, 1.0, 6.5, 0.0, 7.5, 0.0, 8.5, 1.0, 9.5, 0.0, 10.5, 1.0, 13.5, 1.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.5, 1.0, 4.5, 1.0, 5.5, 0.0, 6.5, 0.0, 7.5, 1.0, 8.5, 0.0, 9.5, 1.0, 12.5, 1.0, 13.5, 0.0, 15.5, 0.0)
        self.assertTime(13.5)

    def test_step23(self):
        self.doSteps(23)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 4.5, 0.0, 5.5, 1.0, 7.5, 1.0, 8.5, 0.0, 9.5, 1.0, 14.5, 1.0)
        self.assertPath(1, 0.0, 0.0, 3.5, 0.0, 4.5, 1.0, 5.5, 1.0, 6.5, 0.0, 7.5, 0.0, 8.5, 1.0, 9.5, 0.0, 10.5, 1.0, 13.5, 1.0, 14.5, 0.0, 16.0, 0.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.5, 1.0, 4.5, 1.0, 5.5, 0.0, 6.5, 0.0, 7.5, 1.0, 8.5, 0.0, 9.5, 1.0, 12.5, 1.0, 13.5, 0.0, 15.5, 0.0)
        self.assertTime(14.5)

    def test_step24(self):
        self.doSteps(24)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 4.5, 0.0, 5.5, 1.0, 7.5, 1.0, 8.5, 0.0, 9.5, 1.0, 15.5, 1.0)
        self.assertPath(1, 0.0, 0.0, 3.5, 0.0, 4.5, 1.0, 5.5, 1.0, 6.5, 0.0, 7.5, 0.0, 8.5, 1.0, 9.5, 0.0, 10.5, 1.0, 13.5, 1.0, 14.5, 0.0, 16.0, 0.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.5, 1.0, 4.5, 1.0, 5.5, 0.0, 6.5, 0.0, 7.5, 1.0, 8.5, 0.0, 9.5, 1.0, 12.5, 1.0, 13.5, 0.0, 15.5, 0.0)
        self.assertTime(15.5)

    def test_step25(self):
        self.doSteps(25)
        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 4.5, 0.0, 5.5, 1.0, 7.5, 1.0, 8.5, 0.0, 9.5, 1.0, 15.5, 1.0, 16.5, 0.0, 17.0, 0.0)
        self.assertPath(1, 0.0, 0.0, 3.5, 0.0, 4.5, 1.0, 5.5, 1.0, 6.5, 0.0, 7.5, 0.0, 8.5, 1.0, 9.5, 0.0, 10.5, 1.0, 13.5, 1.0, 14.5, 0.0, 16.0, 0.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.5, 1.0, 4.5, 1.0, 5.5, 0.0, 6.5, 0.0, 7.5, 1.0, 8.5, 0.0, 9.5, 1.0, 12.5, 1.0, 13.5, 0.0, 16.5, 0.0)
        self.assertTime(16.0)

    def test_coalesceRisingSegments(self):
        x = Gate([0], True, (1, 1, 1), NOT)
        y = Gate([1], False, (1, 1, 1), NOT)
        z = Gate([0, 1], False, (1, 2, 2), OR)
        self.runner = PathRunner([x, y, z])

        self.doSteps(3)

        self.assertPath(0, 0.0, 1.0, 1.0, 1.0, 2.0, 0.0, 2.5, 0.0, 3.5, 1.0)
        self.assertPath(1, 0.0, 0.0, 1.0, 0.0, 2.0, 1.0, 2.5, 1.0, 3.5, 0.0)
        self.assertPath(2, 0.0, 0.0, 1.0, 0.0, 3.0, 1.0, 4.0, 1.0)

    def test_coalesceFallingSegments(self):
        x = Gate([0], True, (1, 1, 1), NOT)
        y = Gate([1], False, (1, 1, 1), NOT)
        z = Gate([0, 1], True, (1, 2, 2), NOR)
        self.runner = PathRunner([x, y, z])

        self.doSteps(3)

        self.assertPath(0, 0.0, 1.0, 1.0, 1.0, 2.0, 0.0, 2.5, 0.0, 3.5, 1.0)
        self.assertPath(1, 0.0, 0.0, 1.0, 0.0, 2.0, 1.0, 2.5, 1.0, 3.5, 0.0)
        self.assertPath(2, 0.0, 1.0, 1.0, 1.0, 3.0, 0.0, 4.0, 0.0)

    def test_differentRiseAndFallTimes(self):
        x = Gate([0], True, (1, .5, .25), NOT)
        self.runner = PathRunner([x])

        self.doSteps(5)

        self.assertPath(0, 0.0, 1.0, 1.0, 1.0, 1.25, 0.0, 2.125, 0.0, 2.625, 1.0, 3.375, 1.0, 3.625, 0.0, 4.375, 0.0)

    def test_zeroRiseAndFallTimes(self):
        p = Gate([1, 2], True, (1, 0, 0), OR)
        q = Gate([2], False, (1, 0, 0), COPY)
        r = Gate([0, 1], False, (1, 0, 0), XOR)
        self.runner = PathRunner([p, q, r])

        self.doSteps(5)

        self.assertPath(0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0, 2.0, 0.0, 2.0, 1.0, 4.0, 1.0, 4.0, 0.0, 5.0, 0.0, 5.0, 1.0, 6.0, 1.0)
        self.assertPath(1, 0.0, 0.0,                     2.0, 0.0, 2.0, 1.0, 3.0, 1.0, 3.0, 0.0, 5.0, 0.0, 5.0, 1.0, 6.0, 1.0)
        self.assertPath(2, 0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 2.0, 1.0, 2.0, 0.0, 4.0, 0.0, 4.0, 1.0, 5.0, 1.0, 5.0, 0.0, 6.0, 0.0)

    def test_simpleTruncation(self):
        self.runner.truncate_at(F(3.5))

        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 3.5, 0.0)
        self.assertPath(1, 0.0, 0.0, 3.5, 0.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.5, 1.0)
        self.assertTime(3.5)

    def test_truncationWithInterpolation(self):
        self.runner.truncate_at(F(3.25))

        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 3.25, 0.0)
        self.assertPath(1, 0.0, 0.0, 3.25, 0.0)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.25, 0.75)
        self.assertTime(3.25)

    def test_truncationAtInstantaneousTransition(self):
        x = Gate([0], True, (1, 0, 0), NOT)
        self.runner = PathRunner([x])

        self.runner.truncate_at(F(2.0))

        self.assertPath(0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0, 2.0, 0.0)
        self.assertTime(2.0)

    def test_truncateAgainAtLargerTime(self):
        self.runner.truncate_at(F(3.5))
        self.runner.truncate_at(F(4.25))

        self.assertPath(0, 0.0, 1.0, 1.5, 1.0, 2.5, 0.0, 4.25, 0.0)
        self.assertPath(1, 0.0, 0.0, 3.5, 0.0, 4.25, 0.75)
        self.assertPath(2, 0.0, 0.0, 2.5, 0.0, 3.5, 1.0, 4.25, 1.0)
        self.assertTime(4.25)

    def test_fixForTransitionTimingBug(self):
        p = Gate([1, 2], True, (1.5, .5, .25), OR)
        q = Gate([2], False, (.5, .25, .125), COPY)
        r = Gate([0, 1], False, (2, .75, .5), XOR)
        self.runner = PathRunner([p, q, r])

        self.runner.truncate_at(F(20.0))
        self.assertTime(20.0)

    def doSteps(self, steps):
        for step in range(0, steps):
            self.runner.step()

    def assertTime(self, time):
        self.assertEqual(F(time), self.runner.get_time())

    def assertPath(self, g, *tvs):
        self.assertEqual(len(tvs) % 2, 0)
        expectedPath = []
        for i in range(0, len(tvs) // 2):
            t = tvs[2 * i]
            v = tvs[2 * i + 1]
            expectedPath.append((F(t), F(v)))
        self.assertEqual(self.runner.get_path(g), expectedPath)


if __name__ == '__main__':
    unittest.main()
