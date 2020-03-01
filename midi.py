# External modules
from pypianoroll import Multitrack, Track, load
from math import log, floor
import numpy as np
import json

# Internal modules
from ca import (
    print_states,
    learn_rules_from_states,
    run,
    eca,
    DEFAULT_SEQUENCE_STEPS,
    image_from_states,
)
from stats import metrics
from sampling import random_walk_sampler
from scales import MAJ_SCALES_MIDI_NOTES, CHROMATIC_SCALE

DEFAULT_BEAT_DURATION = 8


def generate_pianoroll(
    states,
    steps=DEFAULT_SEQUENCE_STEPS,
    beat_duration=DEFAULT_BEAT_DURATION,
    scale=MAJ_SCALES_MIDI_NOTES[0],
):
    pianoroll = np.zeros((steps * beat_duration, 128))

    for t in range(steps):
        state = states[t]
        beat = scale * np.array(state)
        beat_list = beat.astype(int).tolist()
        beat_idx = t * beat_duration
        pianoroll[beat_idx, beat_list] = 100

    # Clear 0s
    pianoroll[0 : (steps * beat_duration), 0] = 0

    return pianoroll


def squash_piano_roll_to_chromatic_frames(states):
    width = len(states[0])
    state_slices = floor(width / 12)
    slices = []
    states_arr = np.array(states)
    for i in range(state_slices):
        l = i * 12
        r = l + 12
        slices.append(states_arr[:, l:r])
    s_compressed = np.concatenate(slices)
    return s_compressed


def write_states_to_file(states, f_name):
    states_dict = {"states": [np.array(s).astype(int).tolist() for s in states]}

    with open(f_name, "w") as json_file:
        json.dump(states_dict, json_file)

    print("Wrote file: ", f_name)


def write_files_from_states(
    states,
    metrics,
    seed,
    kernel,
    f_name="./renderings/midi/t",
    title="my awesome piano",
    g=generate_pianoroll,
    steps=DEFAULT_SEQUENCE_STEPS,
    beat_duration=DEFAULT_BEAT_DURATION,
):
    # TODO: make it possible to alter parameters more easily
    pianoroll = g(states, steps, beat_duration)

    # Create a `pypianoroll.Track` instance
    track = Track(pianoroll=pianoroll, program=0, is_drum=False, name=title)

    mt = Multitrack(tracks=[track])

    mid_file = "{f_name}_.{ext}".format(f_name=f_name, ext="mid")
    json_file = "{f_name}_.{ext}".format(f_name=f_name, ext="json")

    # Write MIDI file
    mt.write(mid_file)

    # Write JSON file

    stats = {
        "metrics": metrics,
        # "states": [list(s) for s in states],
        # "seed": list(seed),
        # "kernel": list(kernel),
    }

    print("Writing results: {}".format(json_file))
    # Save state info as json_file
    with open(json_file, "w") as json_file:
        json.dump(stats, json_file)


def convert_midi_to_state(
    f_name, scale_num=None, scale_type="maj", twelve_tone_normalize=True
):
    is_midi = f_name.endswith(".mid") or f_name.endswith(".midi")

    sc_num = scale_num
    sc_type = scale_type

    if scale_num != None:
        scale_mask = get_full_scale(sc_num)
        n = np.array(range(0, 128))
        scale = n[scale_mask]
        print("sc_num: {}, sc_type: {}".format(scale_num, scale_type))

    if is_midi:
        mt = load(f_name)

        # convert to binary representation
        mt.binarize()

        # ensure that the vector is 0,1 only
        track = mt.get_merged_pianoroll(mode="any").astype(int)

        # NOTE: these are the dimensions
        # rows = timestep, cols = keyboard
        # print(track.shape)
        states = []
        for s in track:
            # compress to scale
            if sc_num != None:
                s_compressed = squash_state_to_scale(s, scale_mask)
                states.append(s_compressed)
            else:
                states.append(s)
        if twelve_tone_normalize:
            states = squash_piano_roll_to_chromatic_frames(states)

        if sc_num != None:
            # Squash to scale
            states = [squash_state_to_scale(s, scale_mask[0:12]) for s in states]
        states = list(filter(lambda x: np.sum(x) > 0, states))
        deduped_states = []
        for i, state in enumerate(states):
            if i == 0:
                deduped_states.append(state)
            else:
                # filter out silence
                s = np.sum(state)
                if s > 0 and not np.all(np.equal(state, states[i - 1])):
                    deduped_states.append(state)
        states = deduped_states
    else:
        print("Not midi file!")
        exit(1)

    json_states_file = "{f_name}_states_.{ext}".format(
        f_name=f_name.replace(".", "_"), ext="json"
    )

    write_states_to_file(states, f_name=json_states_file)

    print("Wrote file: ", json_states_file)

    return states


def generate_states_from_rule_and_seed(
    f_name=None,
    rule=None,
    seed=[],
    scale_num=None,
    scale_type="maj",
    states=[],
    steps=DEFAULT_SEQUENCE_STEPS,
):
    sc_num = scale_num
    sc_type = scale_type

    if len(seed):
        width = len(seed)
    else:
        width = 128

    if scale_num != None:
        scale_mask = get_full_scale(sc_num)
        n = np.array(range(0, width))
        scale = n[scale_mask]
        print("sc_num: {}, sc_type: {}".format(scale_num, scale_type))

    # print("WIDTH: ", width, "SC_WIDTH: ", len(scale), scale)

    # Option 1. ECA rule seeds
    # width = len(states[0])
    # seed is initial state
    if len(seed):
        # Squash the seed state to a scale
        squashed_seed = squash_state_to_scale(seed, scale)
        seeds = [squashed_seed]
    else:
        if scale_num != None:
            width = 75
        seed = np.zeros((width,), dtype=int)
        seed[floor(width / 2)] = 1  # add 1 to middle

        # TODO: triad of octaves?
        # seed[floor(width / 2) + 12] = 1  # add 1 to middle
        # seed[floor(width / 2) - 12] = 1  # add 1 to middle

        # Option 0. Random seed
        # seed = np.random.rand(width).round()

        # Option 1. Start from a single 1 value, ala ECA
        seeds = [seed]

        # Option 2. Start from a random given state
        random_state_idx = int(np.random.uniform(0, len(states)))

        rand_state = states[random_state_idx]
        rand_state_tiled = np.tile(rand_state, width)[0:width]
        ## Option 3. Sample states from original
        # seeds = [rand_state_tiled]
        # if sc_num != None:
        #     maj_triad = np.tile(np.array([1, 0, 1, 0, 1, 0, 0]), reps=11)[
        #         0 : (len(states[0]))
        #     ]
        #     seeds.append(maj_triad)

    i = 0

    for seed in seeds:
        print("seed:", seed)
        k = rule["k"]
        a = np.array(rule["rule"])

        # THIS IS SUPER IMPORTANT TO GETTING GOOD RESULTS
        # Flip final bit
        a[-1] = 0

        k_states = np.array(list(map(np.int64, rule["k_states"])))
        # generate rule from k_states / mask
        r_set = k_states[a.astype(bool)]
        print("r_set", r_set)
        r = lambda x, k: eca(x, k, r_set)
        states = run(steps, seed=seed, kernel=k, f=r)

        # apply a filter to the states
        states = random_walk_sampler(states)

        f_name_img = f_name.replace(".", "_") + ".png"
        image_from_states(states, f_name_img)
        print_states(states[0:10])
        mets = metrics(states)
        f_name_out = f_name.replace(".", "_") + "_{}_".format(i)
        if sc_num != None:
            g = lambda x, y, z: generate_pianoroll(x, y, z, scale[0:width])
        else:
            g = lambda x, y, z: generate_pianoroll(x, y, z, CHROMATIC_SCALE)
        write_files_from_states(states, mets, seed, [], f_name_out, g=g)
        i += 1
    return


def write_rule_to_json(rule, f_name):
    json_file = "{f_name}_.{ext}".format(f_name=f_name, ext="json")
    d = {}
    d["k"] = rule["k"]
    d["k_states"] = list(map(str, rule["k_states"]))
    d["rule"] = rule["rule"]
    d["confidence_scores"] = rule["confidence_scores"]
    print(d)
    print("Writing Rule to: {}".format(json_file))
    # Save state info as json_file
    with open(json_file, "w") as json_file:
        json.dump(d, json_file)


def learn_rule_from_file(
    f_name,
    track_num=None,
    scale_num=None,
    scale_type="maj",
    k_radius=1,
    skip_write=False,
    max_states=-1,
):
    is_midi = f_name.endswith(".mid") or f_name.endswith(".midi")
    is_json = f_name.endswith(".json")

    sc_num = scale_num
    sc_type = scale_type

    should_learn_scale_from_states = False

    if scale_num != None:
        scale_mask = get_full_scale(sc_num)
        n = np.array(range(0, 128))
        scale = n[scale_mask]
        print("sc_num: {}, sc_type: {}".format(scale_num, scale_type))
    else:
        # Learn scale from states
        should_learn_scale_from_states = True

    unsquashed_states = []

    if is_midi:
        unsquashed_states = convert_midi_to_state(
            f_name, None, scale_type, twelve_tone_normalize=False
        )
        states = convert_midi_to_state(f_name, None, scale_type)
        # states = unsquashed_states
        # TODO: make this work
        # if should_learn_scale_from_states:
        #     scale = learn_scale_from_twelve_note_normalized_states(states)
        #     print("LEARNED SCALE: ", scale)
    elif is_json:
        # handle json
        with open(f_name, "r") as json_file:
            d = json.load(json_file)
        states = d["states"]
    else:
        print("File extension not supported!")
        exit(1)
    print_states(states[0:5])
    # return
    # mets = metrics(states)
    print("States read from file: ", f_name)
    # print(mets, learn_rules_from_states)

    if max_states > -1:
        states = states[0:max_states]

    rule = learn_rules_from_states(states, k_radius)

    if not skip_write:
        write_rule_to_json(rule, f_name.replace(".", "_rule_"))

    # Choose a state from the midi file randomly as a seed
    # if unsquashed_states:
    #     state_idxs = list(range(len(unsquashed_states)))
    #     # TODO: add guard against empty states
    #     seed_state = unsquashed_states[np.random.choice(state_idxs)]
    #     # if np.sum(seed_state) == 0:
    #     #     seed_state[n]
    #     seed = seed_state
    # else:
    #     seed = []

    seed = []

    # TODO: remove from this function later
    generate_states_from_rule_and_seed(
        f_name=f_name,
        seed=seed,
        rule=rule,
        scale_num=sc_num,
        scale_type=sc_type,
        states=states,
    )

    return rule, states
