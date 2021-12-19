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
