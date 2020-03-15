import glob
import json
import re
from bitarray import bitarray, util

TEST_BASE = "./test_data"
TEST_DIR = "{}/eca_8bit".format(TEST_BASE)
TENDRIL_SUFFIX = ".tendril_states.json"
RULE_SUFFIX = ".rule.json"
TEST_RULE_GLOB = "{}/r_*{}.rule.json".format(TEST_DIR, TENDRIL_SUFFIX)
STATES_FILE_GLOB = "{}/r_*.rule.json{}".format(TEST_DIR, TENDRIL_SUFFIX)
files = glob.glob(TEST_RULE_GLOB)
states_files = glob.glob(STATES_FILE_GLOB)


def parse_file(f_name):
    d = {}
    with open(f_name, "r") as f:
        d = json.load(f)
    return d


def rule_to_int(rule):
    bit_str = "".join(list(map(str, rule)))
    ba = bitarray(bit_str)
    i = util.ba2int(ba)
    return i


def write_results(results):
    f_name = TEST_BASE + "/results.json"
    with open(f_name, "w") as f:
        json.dump(results, f)


def check_result(result, states_dict):
    r_expected = result["expected"]
    r_actual = result["actual"]
    # Compare for int
    if r_expected == r_actual:
        return True
    # Check for ambiguous states
    else:
        s_expected = states_dict[r_expected]
        s_actual = states_dict[r_actual]
        # Ambiguous states
        if s_expected == s_actual:
            return True
        else:
            return False


# Get all states by rule:

states_by_rule_int = {}

for f in states_files:
    d = parse_file(f)
    m = re.findall(r"r_\d+", f)
    if m:
        n = int(m[0].split("_")[1])
    # print(f)
    states_by_rule_int[n] = d["states"]

results = {}

for f in files:
    f1 = f.replace(TENDRIL_SUFFIX + RULE_SUFFIX, "")  # actual
    f2 = f  # generated file
    d1 = parse_file(f1)
    d2 = parse_file(f2)
    r1 = d1["rule"]
    r2 = d2["rule"]
    r1i = rule_to_int(r1)
    r2i = rule_to_int(r2)
    results[f1] = {
        "expected": r1i,
        "actual": r2i,
        "expected_bits": r1,
        "actual_bits": r2,
        "data": d1,
        "data": d2,
    }

write_results(results)

# generate score
total = len(results.keys())
matched = 0
for k in results:
    result = results[k]
    if check_result(result, states_by_rule_int):
        matched += 1

print("score: {}".format(matched / total))
