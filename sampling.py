import numpy as np


def noop(states):
    return states


def random_walk_sampler(states):
    """
    Use random-walk strategy for sampling bits from the state space
    """

    height = len(states)
    width = len(states[0])
    voices = 2

    # generate empty states array
    result = [np.zeros((width,)) for i in range(0, height)]

    ## Strategy 1:  Follow a 1-bit path, once per "voice"
    for v in range(0, voices):
        cursor = 0
        for i in range(0, height):
            ith_state = states[i]
            # print("ith_state", ith_state, cursor)
            s = result[i]
            bit = 0
            j = cursor
            if np.random.rand() > 0.5:
                step = -1
            else:
                step = 1
            # find location of first on bit
            while j in range(0, width):
                if ith_state[j]:
                    cursor = j
                    bit = 1
                    break
                j += step
            if not bit:
                continue
                # print("No bit set!")
            else:
                s[cursor] = bit
    return result


__all__ = ["noop", "random_walk_sampler"]

