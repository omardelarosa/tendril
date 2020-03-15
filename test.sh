#!/bin/bash

# Generate all 256 ECA rules

for f in examples/rules/eca_8bit/*
do
    python main.py \
        --generateFrom $f \
        --seed examples/seeds/seed_32x1_1bit_active.json \
        --json \
        --png \
        --sampler=noop \
        --steps 32
done