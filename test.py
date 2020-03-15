import glob
import json
from bitarray import bitarray, util

TEST_BASE = "./test_data"
TEST_DIR = "{}/eca_8bit".format(TEST_BASE)
TENDRIL_SUFFIX = ".tendril_states.json"
RULE_SUFFIX = ".rule.json"
TEST_RULE_GLOB = "{}/r_*{}.rule.json".format(TEST_DIR, TENDRIL_SUFFIX)

files = glob.glob(TEST_RULE_GLOB)


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

    # print("files: {}, {}".format(f1, f2))
    # print("\t: {} = {} == {}".format(r1i == r2i, r1i, r2i))
    # print("generated", f1, d1["rule"])
    # print("original", f2, d2["rule"])

# print(results)
write_results(results)

# generate score
total = len(results.keys())
matched = 0
for k in results:
    result = results[k]
    if result["expected"] == result["actual"]:
        matched += 1

print("score: {}".format(matched / total))
