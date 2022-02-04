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

from fractions import Fraction


class Gate:
    def __init__(self, inputs, initial_value, timings, function, label=None):
        if len(timings) == 3:
            lag_time = Fraction(timings[0])
            rise_time = Fraction(timings[1])
            fall_time = Fraction(timings[2])
        elif len(timings) == 2:
            propagation_delay = Fraction(timings[0])
            transition_factor = Fraction(timings[1])
            transition_time = propagation_delay * transition_factor
            lag_time = propagation_delay - transition_time / 2
            rise_time = transition_time
            fall_time = transition_time
        else:
            raise ValueError
        if any(input < 0 for input in inputs) or lag_time <= 0 or rise_time < 0 \
                or fall_time < 0:
            raise ValueError
        self.inputs = inputs
        self.initial_value = initial_value
        self.lag_time = lag_time
        self.rise_time = rise_time
        self.fall_time = fall_time
        self.function = function
        self.label = label
