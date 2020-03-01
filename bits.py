import numpy as np


def uint8_tuple_to_bin_arr(t):
    """
    Convert a uint8 tuple into an array of booleans.
    """
    return np.unpackbits(np.array(t, dtype=np.uint8))


def encode_state(s):
    """
    Encode binary state as a tuple
    """
    bool_arr = np.array(s, dtype=np.bool)
    x = np.packbits(bool_arr)
    x_t = tuple(x)
    # x_s = str(x_t)
    # Tuple and string representation
    return x_t


def decode_state(s_t):
    """
    Decode from tuple
    """
    x_t = np.unpackbits(np.array(s_t, dtype=np.uint8))
    return x_t
