import pyphi
import numpy as np
import sys

height = int(sys.argv[1])
width = int(sys.argv[2])
size = width * height

print(f"Generating {height}x{width} XOR grid")

def col_for(pos):
    return pos % width

def row_for(pos):
    return pos // width

def pos_for(row, col):
    return (row % height) * width + (col % width)

def xor_for(pos, state):
    row = row_for(pos)
    col = col_for(pos)
    return state[pos_for(row-1, col)] ^ state[pos_for(row, col-1)] 
    #return state[pos_for(row-1, col)] \
    #        ^ state[pos_for(row+1, col)] \
    #        ^ state[pos_for(row, col-1)] \
    #        ^ state[pos_for(row, col+1)] 

def print_states(old_state, new_state):
    for row in range(height):
        print("[" + ",".join((str(old_state[pos_for(row,col)]) for col in range(width)))
                + "] - [" + ",".join((str(new_state[pos_for(row,col)]) for col in range(width)))
                + "]")

tpm = []
for index in range(2 ** size):
    state = pyphi.convert.le_index2state(index, size)
    new_state = [
        xor_for(pos, state)
        for pos in range(size)
    ]
    print(f"===== {index} =====")
    print_states(state, new_state)
    print()
    tpm.append(new_state)

network = pyphi.Network(tpm)

for index in range(2 ** size):
    state = pyphi.convert.le_index2state(index, size)
    new_state = [
        xor_for(pos, state)
        for pos in range(size)
    ]
    print(f"===== {index} =====")
    print_states(state, new_state)
    try:
        subsystem = pyphi.Subsystem(network, state)
        print(pyphi.compute.phi(subsystem))
    except pyphi.exceptions.StateUnreachableError:
        print("Unreachable")
    print()
    

# state = [0] * size


# print(tpm)


# TODO: precompute connectivity matrix as well
# TODO: output Python code for tpm & cm for sharing with pyphi-users (or Larissa)
