def rel_gate(
        inputs, initial_value, propagation_delay, transition_factor, function):
    transition_time = propagation_delay * transition_factor
    lag_time = propagation_delay - transition_time / 2
    return Gate(inputs, initial_value, lag_time,
            transition_time, transition_time, function)


class Gate:
    def __init__(self,
            inputs, initial_value, lag_time, rise_time, fall_time, function):
        if any(input < 0 for input in inputs) or lag_time <= 0 or rise_time < 0 \
                or fall_time < 0:
            raise ValueError
        self.inputs = inputs
        self.initial_value = initial_value
        self.lag_time = lag_time
        self.rise_time = rise_time
        self.fall_time = fall_time
        self.function = function
