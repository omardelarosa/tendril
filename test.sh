#!/bin/bash

# Make directories for output
rm -rf test_data
mkdir test_data
mkdir test_data/eca_8bit

# Generate all 256 ECA rules
python main.py \
    --generateAllRules test_data/eca_8bit \
    --kernelRadius=1

# Generate states from each rule
for f in test_data/eca_8bit/*.rule.json
do
    # # generate states from rule
    python main.py \
        --generateFrom $f \
        --seed examples/seeds/seed_32x1_1bit_active.json \
        --json \
        --png \
        --sampler=noop \
        --steps=32

    # # learn rule from the generated states
    python main.py \
        --learn "$f.tendril_states.json" \
        --json \
        --kernelRadius=1
done