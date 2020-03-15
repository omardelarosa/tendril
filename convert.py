from PIL import Image
import numpy as np
import os
import math

from midi import write_states_to_file, convert_midi_to_state, write_rule_to_json
from ca import generate_k_states_from_k_radius, generate_rule_from_k_states

# TODO: add 12-tone normalize
def convert(f_name):
    _, ext = os.path.splitext(f_name)
    states = None
    if ext == ".png":
        states = convert_png_to_states(f_name)
    elif ext in [".mid", ".midi"]:
        states = convert_midi_to_state(
            f_name,
            scale_num=None,
            scale_type="maj",
            twelve_tone_normalize=False,
            save_midi=False,
            save_json=False,
        )
    else:
        print("Unsupported file extension: {}".format(ext))
        exit(1)

    if not states:
        print("No states can be derived from {}".format(f_name))
        print("Please ensure this file is supported.")
        exit(1)

    # Write states to json
    json_states_file = "{f_name}.{ext}".format(
        f_name=(f_name + ".training_states"), ext="json"
    )

    write_states_to_file(states, json_states_file)


def convert_png_to_states(f_name):
    im = Image.open(f_name)
    im_arr = np.array(im)
    states = []
    ALIVE = 0  # black
    DEAD = 255  # white
    # arr = im_arr[im_arr_zeros].astype(int)
    # print(im_arr)
    for row in im_arr:
        state = np.zeros((len(row),), dtype=int)
        for i in range(len(row)):
            el = row[i]
            if el == ALIVE:
                state[i] = 1
        states.append(state)
        print(state)
    return states


def generate_all_rules_for_k(out_dir="", k_radius=None, debug=False):
    n = 2  # number of states per cell
    k_len = (k_radius * 2) + 1
    activation_size = n ** k_len
    num_rules = n ** activation_size

    print(
        "k_radius: {}, activation_size: {}, num_rules: {}, k_len: {}".format(
            k_radius, activation_size, num_rules, k_len
        )
    )
    # # max int rules
    if k_len >= 5:
        print(
            "Warning: large rule space selected {}.  Consider selecting a smaller rule space.".format(
                k_len
            )
        )

    k_states = generate_k_states_from_k_radius(k_radius)

    digits_to_pad = math.ceil(math.log(num_rules, 10))
    for r in range(0, num_rules):
        if debug:
            print("Computing rule: {}".format(r))
        rule = generate_rule_from_k_states(k_states, k_radius, r, debug=debug)
        r_str = str(r).zfill(digits_to_pad)
        f_name = "{}/r_{}".format(out_dir, r_str)
        write_rule_to_json(rule, f_name, debug)
