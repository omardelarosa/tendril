import numpy as np
from scipy.ndimage import convolve
from bits import uint8_tuple_to_bin_arr, encode_state
from math import log, floor
from PIL import Image
import bitarray

DEFAULT_SEQUENCE_STEPS = 96
DEFAULT_SEED_SHAPE = (32,)
DEFAULT_SEED = np.zeros(DEFAULT_SEED_SHAPE, dtype=int)
DEFAULT_SEED[floor(DEFAULT_SEED_SHAPE[0] / 2)] = 1  # Activate a single middle bit

DEFAULT_PHI = np.array([1, 10, 100])  # A generic 3x1 conv kernel to be used as phi


def wrapped_convolver(x, k):
    """
    Default lambda that applies a convolution "wrapped"
    """
    x_next = convolve(x, k, mode="wrap")
    x_norm = np.linalg.norm(x_next)
    if x_norm == 0:
        return x
    return np.abs(np.round(x_next / x_norm))


def print_states(states):
    for i in range(len(states)):
        print("{}: {}".format(i, states[i]))


def tens(n):
    """
    Return a list of all powers of 10, 0 to n
    """
    ns = [1]
    if n == 1:
        return ns
    for i in range(1, n):
        ns.append(10 ** i)
    return ns


def run(
    steps=DEFAULT_SEQUENCE_STEPS,
    seed=DEFAULT_SEED,
    kernel=DEFAULT_PHI,
    f=wrapped_convolver,
):
    results = [seed]
    a_b = np.copy(seed)
    # print("{}: {}".format(0, seed))
    for i in range(steps):
        a_b = f(a_b, kernel)
        r = a_b.copy()
        # print("{}: {}".format(i + 1, r))
        results.append(r)
    return results


def image_from_states(states, f_name, max_height=64):
    mat = np.array(np.uint8(np.logical_not(states[0:max_height])) * 255)
    im = Image.fromarray(mat, mode="L")
    print("saving image: ", f_name)
    im.save(f_name)
    return im


def eca(x, k, r_set):
    """
    Elementary cellular automata lambda

    k: kernel operator
    a: activation
    k_states: kernel combination space
    """
    x_next = convolve(x, k, mode="constant", cval=0.0)
    matches = np.isin(x_next, r_set)
    result = np.where(matches, 1, 0)
    return result


def learn_rules_from_states(states, kernel_radius=1, debug=False):
    """
    CARLA algorithm applied to the sequence of states
    """
    # generate a kernel based on radius
    k_len = (kernel_radius * 2) + 1
    # kernel = primes(k_len)
    k = tens(k_len)

    num_bits_kernel = 2 ** (len(k))

    k_states = [uint8_tuple_to_bin_arr((i,)) for i in range(0, num_bits_kernel)]
    k_states_trimmed = list(
        map(lambda x: x[-int(log(num_bits_kernel, 2)) :], [x for x in k_states])
    )
    k_states_trimmed.reverse()  # sort by sums
    if debug:
        print("k_space_size: ", len(k_states))

    k_states = list(map(lambda x: np.dot(k, x), k_states_trimmed))

    # the maximum length of the rule, aka 2^(len(k))
    activations_search_space_size = 2 ** num_bits_kernel

    if debug:
        print("rule_space_size: ", activations_search_space_size)

    # print("k_states: ", k_states)
    # only track non-zero
    counts_dict = {}
    # for key in k_states:
    # count number of next states, 0 = Falses, 1 = Trues
    # counts_dict[key] = [0, 0]

    # 1. iterate over all states learning transitions
    n = len(states)
    for i in range(n - 1):
        x = states[i]
        x_plus_1 = states[i + 1]
        # Apply kernel to x
        x_pattern = convolve(x, k, mode="constant")
        # compare patterns to next state value
        for j in range(len(x)):
            x_patt_i = x_pattern[j]  # pattern encoding
            # print("x_patt_i", x_patt_i)
            rule_str = str(int(x_patt_i))
            x_plus_1_j = int(x_plus_1[j])  # next transition
            # print("r({}) {} -> {}: ".format(rule_str, x_patt_i, x_plus_1_j))
            # return
            if rule_str in counts_dict:
                counts_dict[rule_str][x_plus_1_j] = (
                    counts_dict[rule_str][x_plus_1_j] + 1
                )
            else:
                counts = [0, 0]
                counts[x_plus_1_j] = 1
                counts_dict[rule_str] = counts

        # Find match for x-pattern

    # create a dictionary of likelihood value will be 1
    rule = {}
    targets = {}
    state_size = len(states[0])
    population = np.sum(np.array(states))  # i.e. number of alive cells
    occurences = n * len(states[0])
    if debug:
        print(counts_dict)

    # the minimum probability to mark rule
    prob_floor = 0.0000
    for n in counts_dict:
        v = counts_dict[n]
        # rule[n] = np.float64(v[1]) / np.sum(v, dtype=np.float64)
        prob_1 = np.float64(v[1]) / population
        prob_0 = np.float64(v[0]) / (occurences - population)
        target = 0
        if prob_1 > prob_0:
            prob = prob_1
            target = 1
        else:
            prob = prob_0
            target = 0
        # assign the prob
        if prob > prob_floor:
            rule[n] = prob
            targets[n] = target
    # Match with rule in rulespace
    a = []
    for ks in k_states:
        rule_str = str(ks)
        # print("rule_str: ", rule_str)
        if rule_str in rule:
            t = targets[rule_str]
            # print("t:", t)
            a.append(t)
        else:
            a.append(0)
    # print("a:", a, "rule:", rule)
    return {"k": k, "rule": a, "k_states": k_states, "confidence_scores": rule}


def generate_k_states_from_k_radius(kernel_radius):
    k_len = (kernel_radius * 2) + 1
    # kernel = primes(k_len)
    k = tens(k_len)

    num_bits_kernel = 2 ** (len(k))

    k_states = [uint8_tuple_to_bin_arr((i,)) for i in range(0, num_bits_kernel)]
    k_states_trimmed = list(
        map(lambda x: x[-int(log(num_bits_kernel, 2)) :], [x for x in k_states])
    )
    k_states_trimmed.reverse()  # sort by sums

    k_states = list(map(lambda x: np.dot(k, x), k_states_trimmed))

    return k_states


def generate_rule_from_k_states(k_states, kernel_radius, rule_number: int, debug=False):
    k_len = (kernel_radius * 2) + 1
    k = tens(k_len)
    expected_activation_size = 2 ** k_len  # for 2-state cells
    # Parse bit number
    fmt = str(expected_activation_size).zfill(3) + "b"
    bit_str = format(rule_number, fmt)

    activation = np.array(bitarray.bitarray(bit_str).tolist()).astype(int).tolist()
    activation_size = len(activation)

    if debug:
        print("bitstr", bit_str, activation)
    # K len
    if activation_size > expected_activation_size:
        print(
            "Rule size {} does not match expected kernel length of {}".format(
                activation_size, k_len
            )
        )

    rule = {
        "k": k,
        "rule": activation,
        "k_states": k_states,
        "confidence_scores": {},  # not supported
    }

    if debug:
        print(rule)

    return rule

