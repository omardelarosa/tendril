# External modules
from pypianoroll import Multitrack, Track, load
from math import log, floor
import numpy as np
import json
import sampling

# Internal modules
from ca import (
    print_states,
    learn_rules_from_states,
    run,
    eca,
    DEFAULT_SEQUENCE_STEPS,
    image_from_states,
    DEFAULT_SEED,
)
from stats import metrics
from scales import MAJ_SCALES_MIDI_NOTES, MIN_SCALES_MIDI_NOTES, CHROMATIC_SCALE

DEFAULT_BEAT_DURATION = 8


def get_seed_from_file(f_name):
    seed_file_dict = {}
    with open(f_name, "r") as json_file:
        seed_file_dict = json.load(json_file)

    seed = np.array(seed_file_dict["seed"])

    # Case 1: 2-d or >
    if len(seed.shape) > 1:
        # Choose a random row from seed matrix
        idx = np.random.randint(0, len(seed))
        return seed[idx]
    # Case 2: 1-d
    else:
        return seed


def get_rule_from_file(f_name):
    rule_file_dict = {}
    with open(f_name, "r") as json_file:
        rule_file_dict = json.load(json_file)

    rule = np.array(rule_file_dict["rule"])
    k = np.array(rule_file_dict["k"])
    k_states = np.array(list(map(int, rule_file_dict["k_states"])))
    confidence_scores = rule_file_dict["confidence_scores"]
    # TODO: add coocurrence table for each state
    return {
        "k": k,
        "rule": rule,
        "k_states": k_states,
        "confidence_scores": confidence_scores,
    }


def squash_state_to_scale(state, sc_mask):
    s_compressed = state[sc_mask]
    return s_compressed


def map_ca_state_to_scale(state, scale):
    return state * scale


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

    print("writing states to file: ", f_name)


def write_files_from_states(
    states,
    metrics,
    seed,
    kernel,
    f_name="./renderings/midi/t",
    title="tendril sequence",
    g=generate_pianoroll,
    steps=DEFAULT_SEQUENCE_STEPS,
    beat_duration=DEFAULT_BEAT_DURATION,
    save_json=False,
    save_midi=False,
    debug=False,
):
    # TODO: make it possible to alter parameters more easily
    pianoroll = g(states, steps, beat_duration)

    # Create a `pypianoroll.Track` instance
    track = Track(pianoroll=pianoroll, program=0, is_drum=False, name=title)

    mt = Multitrack(tracks=[track])

    mid_file = "{f_name}.tendril.{ext}".format(f_name=f_name, ext="mid")
    json_file = "{f_name}.tendril_states.{ext}".format(f_name=f_name, ext="json")

    # Write MIDI file
    if save_midi:
        print("writing midi file to: ", mid_file)
        mt.write(mid_file)

    # Write JSON file
    stats = {
        "metrics": metrics,
    }

    if json_file:
        print("writing tendril states to: {}".format(json_file))
        # Save state info as json_file
        with open(json_file, "w") as json_file:
            json.dump(stats, json_file)


def convert_midi_to_state(
    f_name,
    scale_num=None,
    scale_type="maj",
    twelve_tone_normalize=True,
    save_midi=False,
    save_json=False,
):
    is_midi = f_name.endswith(".mid") or f_name.endswith(".midi")

    sc_num = scale_num
    sc_type = scale_type

    scale = get_scale(scale_num, scale_type)

    if is_midi:
        mt = load(f_name)

        # convert to binary representation
        mt.binarize()

        # ensure that the vector is 0,1 only
        track = mt.get_merged_pianoroll(mode="any").astype(int)

        # NOTE: these are the dimensions
        states = []
        for s in track:
            # compress to scale
            states.append(s)
        if twelve_tone_normalize:
            states = squash_piano_roll_to_chromatic_frames(states)

        if sc_num != None:
            # Squash to scale
            states = [squash_state_to_scale(s, CHROMATIC_SCALE[0:12]) for s in states]
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
        print("Not midi file: {}".format(f_name))
        exit(1)

    json_states_file = "{f_name}.{ext}".format(
        f_name=(f_name + ".training_states"), ext="json"
    )

    if save_json:
        write_states_to_file(states, f_name=json_states_file)

    return states


def get_scale(scale_num=None, scale_type="min", debug=False):
    if scale_num != None:
        if scale_type == "min":
            scale = MIN_SCALES_MIDI_NOTES[scale_num]
        else:
            scale = MAJ_SCALES_MIDI_NOTES[scale_num]
    else:
        scale = CHROMATIC_SCALE
        scale_num = "--"
        scale_type = "chromatic"

    if debug:
        print("sc_num: {}, sc_type: {}".format(scale_num, scale_type))

    return scale


def generate_states_from_rule_and_seed(
    f_name=None,
    rule=None,
    seed=[],
    scale_num=None,
    scale_type="maj",
    states=[],
    steps=DEFAULT_SEQUENCE_STEPS,
    sampler_name=None,
    debug=False,
    save_png=False,
    save_json=False,
    save_midi=False,
    beat_duration=DEFAULT_BEAT_DURATION,
):
    sc_num = scale_num
    sc_type = scale_type

    if len(seed):
        width = len(seed)
    else:
        width = 128

    scale = get_scale(scale_num, scale_type, debug)

    if not len(seed):
        # Start from a default seed with 1 activated bit
        seed = DEFAULT_SEED

    k = rule["k"]
    a = np.array(rule["rule"])

    # THIS IS SUPER IMPORTANT TO GETTING GOOD RESULTS.  It prevents [0,0,0] -> 1 transitions which clutter up CA
    # Flip final bit
    a[-1] = 0

    k_states = np.array(list(map(np.int64, rule["k_states"])))
    print("seed: {}, k: {}: k_states: {}".format(seed, k, k_states))

    # generate rule from k_states / mask
    r_set = k_states[a.astype(bool)]
    print("r_set: {}".format(r_set))
    r = lambda x, k: eca(x, k, r_set)

    states = run(steps, seed=seed, kernel=k, f=r)

    # apply a sampling filter to the states.
    if sampler_name:
        sampler = getattr(sampling, sampler_name)
        states = sampler(states)

    # TODO: add a conditional flag for image generation
    if save_png:
        f_name_img = f_name + ".tendril.png"
        image_from_states(states, f_name_img)
    if debug:
        print_states(states[0:10])
    mets = metrics(states)

    # g(states, steps, beat_duration)
    if sc_num != None:
        g = lambda x, y, z: generate_pianoroll(x, y, z, scale[0:width])
    else:
        g = lambda x, y, z: generate_pianoroll(x, y, z, CHROMATIC_SCALE[0:width])

    if save_json or save_midi:
        write_files_from_states(
            states,
            mets,
            seed,
            [],
            f_name,
            g=g,
            save_json=save_json,
            save_midi=save_midi,
            debug=debug,
            beat_duration=beat_duration,
            steps=steps,
        )
    return


def write_rule_to_json(rule, f_name, debug=False):
    json_file = "{f_name}.{ext}".format(f_name=f_name + ".rule", ext="json")
    d = {}
    d["k"] = rule["k"]
    d["k_states"] = list(map(str, rule["k_states"]))
    d["rule"] = rule["rule"]
    d["confidence_scores"] = rule["confidence_scores"]
    if debug:
        print("writing rule from dictionary: ")
        print(d)
    print("writing rule to: {}".format(json_file))
    # Save state info as json_file
    with open(json_file, "w") as json_file:
        json.dump(d, json_file)


def learn_rule_from_file(
    f_name,
    scale_num=None,
    scale_type="maj",
    k_radius=1,
    skip_write=False,
    max_states=-1,
    debug=False,
    save_json=False,
    save_midi=False,
):
    is_midi = f_name.endswith(".mid") or f_name.endswith(".midi")
    is_json = f_name.endswith(".json")

    sc_num = scale_num
    sc_type = scale_type
    scale = get_scale(scale_num, scale_type)

    if is_midi:
        states = convert_midi_to_state(
            f_name, None, scale_type, save_json=save_json, save_midi=save_midi,
        )
    elif is_json:
        # handle json
        with open(f_name, "r") as json_file:
            d = json.load(json_file)
        states = d["states"]
    else:
        print("File extension not supported!")
        exit(1)

    if debug:
        print_states(states[0:5])
        print("States read from file: ", f_name)

    if max_states > -1:
        states = states[0:max_states]

    rule = learn_rules_from_states(states, k_radius)

    write_rule_to_json(rule, f_name)

    return rule, states
