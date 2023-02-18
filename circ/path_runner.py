# Justin's IIT Thesis - Digital Circuit Simulator
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

from fractions import Fraction as F


ONE = F(1)
ZERO = F(0)
ONE_HALF = F(1, 2)


class PathRunner:

    def __init__(self, gates):
        self.gates = gates
        self.paths = []
        for gate in gates:
            path = []
            initial_value = ONE if gate.initial_value else ZERO
            lag_time = gate.lag_time
            path.append((ZERO, initial_value))
            path.append((lag_time, initial_value))
            self.paths.append(path)

    def truncate_at(self, time):
        if any(gate.lag_time > time for gate in self.gates):
            raise ValueError
        while self.get_time() < time:
            self.step()
        for path in self.paths:
            for i in range(len(path) - 1, 0, -1):
                start_t, start_v = path[i - 1]
                end_t, end_v = path[i]
                if start_t >= time:
                    del path[i]
                elif end_t == time:
                    break
                else:
                    assert end_t > time
                    path[i] = (time, start_v + (end_v - start_v)
                                     * (time - start_t) / (end_t - start_t))
                    break

    def get_size(self):
        return len(self.gates)

    def get_path(self, g):
        return self.paths[g]

    def get_time(self):
        return min(path[-1][0] for path in self.paths)

    def step(self):
        time = self.get_time()
        for g in range(0, len(self.gates)):
            gate = self.gates[g]
            path = self.paths[g]
            last_t, last_v = path[-1]
            if last_t == time:
                output_t, output_v = self.compute_output_segment(gate, time)
                current_value = last_v
                target_value = output_v
                assert target_value == 0 or target_value == 1
                if target_value == current_value:
                    self.add_points(g, [(output_t, output_v)])
                elif target_value == 0:
                    end_value = None if gate.fall_time == 0 else \
                            current_value - (output_t - time) / gate.fall_time
                    if end_value is not None and end_value >= 0:
                        self.add_points(g, [(output_t, end_value)])
                    else:
                        cross_time = current_value * gate.fall_time
                        self.add_points(g, [(time + cross_time, ZERO),
                                (output_t, output_v)]);
                else:  # target_value == 1
                    end_value = None if gate.rise_time == 0 else \
                            current_value + (output_t - time) / gate.rise_time
                    if end_value is not None and end_value <= 1:
                        self.add_points(g, [(output_t, end_value)])
                    else:
                        cross_time = (ONE - current_value) * gate.rise_time
                        self.add_points(g, [(time + cross_time, ONE),
                                (output_t, output_v)])

    def add_points(self, g, points):
        path = self.paths[g]
        prior_t, prior_v = path[-1]
        assert points[-1][0] > prior_t
        for point_t, point_v in points:
            assert point_t >= prior_t and 0 <= point_v <= 1
            prior_t, prior_v = point_t, point_v
        for point_t, point_v in points:
            prior_t, prior_v = path[-1]
            earlier_v = path[-2][1] if len(path) > 1 else None
            if earlier_v is not None and (
                    point_v == prior_v and prior_v == earlier_v
                    or point_v > prior_v and prior_v > earlier_v
                    or point_v < prior_v and prior_v < earlier_v):
                path[-1] = (point_t, point_v)
            elif point_t != prior_t or point_v != prior_v:
                path.append((point_t, point_v))

    def compute_output_segment(self, gate, time):
        """Returns (t, v) where the inputs provide a consistent input
           from time to t with target value v."""
        t0 = time - gate.lag_time
        input_segments = [self.compute_input_segment(input, t0)
                          for input in gate.inputs]
        output_b = gate.function([b for t, b in input_segments])
        return (min(t for t, v in input_segments) + gate.lag_time,
                ONE if output_b else ZERO)

    def compute_input_segment(self, g, t0):
        """Returns (t, b) where gate g provides a consistent output
           from time t0 to t with boolean value b."""
        t = t0
        b = None
        path = self.paths[g]

        # optimize for large paths, since we only need the last few segments
        first_index = -1
        for i in range(len(path) - 1, 0, -1):
            if path[i][0] > t0:
                first_index = i - 1
            else:
                break
        assert 0 <= first_index <= len(path) - 2

        for i in range(first_index, len(path) - 1):
            start_t, start_v = path[i]
            end_t, end_v = path[i + 1]
            assert start_v != ONE_HALF or end_v != ONE_HALF
            transition_time = None
            if start_v >= ONE_HALF and end_v >= ONE_HALF:
                start_b = True
                end_b = True
            elif start_v <= ONE_HALF and end_v <= ONE_HALF:
                start_b = False
                end_b = False
            elif start_v > ONE_HALF and end_v < ONE_HALF:
                start_b = True
                end_b = False
                fall_delta = start_v - end_v
                transition_delta = start_v - ONE_HALF
                fall_time = end_t - start_t
                transition_time = start_t + \
                        transition_delta / fall_delta * fall_time
            else:  # start_v < ONE_HALF and end_v > ONE_HALF
                start_b = False
                end_b = True
                rise_delta = end_v - start_v
                transition_delta = ONE_HALF - start_v
                rise_time = end_t - start_t
                transition_time = start_t + \
                        transition_delta / rise_delta * rise_time

            if transition_time is not None and t0 >= transition_time:
                b = end_b;
                t = end_t;
            elif start_t <= t0 or start_b == b:
                b = start_b;
                if end_b != start_b:
                    t = transition_time
                    break
                else:
                    t = end_t;
            else:
                break

        assert t > t0 and b is not None
        return (t, b)
