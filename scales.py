import numpy as np

MINOR_SCALE_MASK = np.array([0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1], bool)
MAJOR_SCALE_MASK = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1], bool)

# C_MAJOR_SCALE_FULL = MAJOR_SCALE_MASK.tile(11)

NUM_SCALES = 12


MIDI_NOTE_MAX = 128
MIDI_NOTE_MIN = 0
MAX_OCTAVES = 12

CHROMATIC_SCALE = np.array(range(MIDI_NOTE_MIN, MIDI_NOTE_MAX))

# Major scales as MIDI note arrays
MAJ_SCALES_MIDI_NOTES = [
    CHROMATIC_SCALE[
        np.tile(MAJOR_SCALE_MASK, MAX_OCTAVES)[
            (MIDI_NOTE_MIN + i) : (MIDI_NOTE_MAX + i)
        ]
    ]
    for i in range(0, NUM_SCALES)
]

# Minor scales as MIDI note arrays
# Major scales as MIDI notes
MIN_SCALES_MIDI_NOTES = [
    CHROMATIC_SCALE[
        np.tile(MINOR_SCALE_MASK, MAX_OCTAVES)[
            (MIDI_NOTE_MIN + i) : (MIDI_NOTE_MAX + i)
        ]
    ]
    for i in range(0, NUM_SCALES)
]

NOTE_LETTER_TO_NUMBER_DICT = {
    "C": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
}
