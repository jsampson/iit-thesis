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

jk = {
    "S": lambda state: state["S"],
    "R": lambda state: state["R"],
    "C": lambda state: state["C"],
    "J": lambda state: state["J"],
    "K": lambda state: state["K"],
    "1": lambda state: not (state["S"] and state["4"] and state["2"]),
    "2": lambda state: not (state["1"] and state["R"] and state["C"]),
    "3": lambda state: not (state["2"] and state["C"] and state["4"]),
    "4": lambda state: not (state["5"] or state["6"]),
    "5": lambda state: state["3"] and state["R"] and state["J"] and state["N"],
    # Note: state["3"] on next line is diff. between spec sheet and text book,
    # but doesn't actually change the resulting stable states
    "6": lambda state: state["R"] and state["K"] and state["Q"] and state["3"],
    "Q": lambda state: not (state["S"] and state["2"] and state["N"]),
    "N": lambda state: not (state["Q"] and state["3"] and state["R"]),
}

def combine(a_states, b_states):
    result = []
    for a in a_states:
        for b in b_states:
            result.append(a + b)
    return result

def all_states_for(key_iter):
    try:
        k = next(key_iter)
    except StopIteration:
        return ("",)
    return combine((k + ".", k + "*"), all_states_for(key_iter))

def all_starting_states():
    return combine(
        ("S.R*C*", "S*R.C*"),
        all_states_for(iter(["J", "K", "1", "2", "3", "4", "5", "6", "Q", "N"]))
    )

def single_step(prior_state, network):
    prior_state_dict = {
        prior_state[i]: prior_state[i + 1] == "*"
        for i in range(0, len(prior_state), 2)
    }
    assert set(prior_state_dict) == set(network)
    next_state = ""
    for i in range(0, len(prior_state), 2):
        key = prior_state[i]
        next_state += key
        next_state += ("*" if network[key](prior_state_dict) else ".")
    return next_state

def stabilize(starting_state, network):
    prior_state = starting_state
    for i in range(100):
        next_state = single_step(prior_state, network)
        if next_state == prior_state:
            return next_state
        prior_state = next_state
    raise Exception("failed to stabilize starting from " + starting_state)

def stable_starting_states():
    seen = set()
    result = []
    for state in all_starting_states():
        stable = stabilize(state, jk)
        if stable not in seen:
            result.append(stable)
            seen.add(stable)
    return result

def stable_post_boot_states():
    states = stable_starting_states()
    for i in range(len(states)):
        state = states[i]
        state = state.replace("S.", "S*")
        state = state.replace("R.", "R*")
        states[i] = stabilize(state, jk)
    return states

def stable_clock_down_after_start_states():
    states = stable_post_boot_states()
    for i in range(len(states)):
        state = states[i]
        state = state.replace("C*", "C.")
        states[i] = stabilize(state, jk)
    return states

def stable_clock_up_states():
    states = stable_clock_down_after_start_states()
    for i in range(len(states)):
        state = states[i]
        state = state.replace("C.", "C*")
        states[i] = stabilize(state, jk)
    return states
