#!/bin/bash

DEFAULT_TEST_OUT_DIR="test_data"
DEFAULT_NUM_STEPS_IN_SEQUENCE=32

TEST_OUT_DIR="${1:-$DEFAULT_TEST_OUT_DIR}"
NUM_STEPS="${2:-$DEFAULT_NUM_STEPS_IN_SEQUENCE}"

# Make directories for output
rm -rf $TEST_OUT_DIR
mkdir $TEST_OUT_DIR
mkdir $TEST_OUT_DIR/eca_8bit

# Generate all 256 ECA rules
python main.py \
    --generateAllRules $TEST_OUT_DIR/eca_8bit \
    --kernelRadius=1

# Generate states from each rule
for f in $TEST_OUT_DIR/eca_8bit/*.rule.json
do
    # # generate states from rule
    python main.py \
        --generateFrom $f \
        --seed examples/seeds/seed_32x1_1bit_active.json \
        --json \
        --png \
        --sampler=noop \
        --steps=$NUM_STEPS \
        --dontIgnoreOdd

    # # learn rule from the generated states
    python main.py \
        --learn "$f.tendril_states.json" \
        --json \
        --kernelRadius=1
done

# Test all the results
python test.py
