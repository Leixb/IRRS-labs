#!/usr/bin/env bash

set -eo pipefail

MAX_FREQ=(0.1 0.2 0.3 0.4 0.5 0.6 0.7)
MIN_FREQ="${MIN_FREQ:-0.0}"
NUM_WORDS="${NUM_WORDS:-250}"

ORIGINAL_PWD="$(pwd)"

RESULTS="${RESULTS:-${ORIGINAL_PWD}/results}"
mkdir -p "${RESULTS}"

SCRIPT="$ORIGINAL_PWD/ExtractData.py"

# Extract the data for each frequency range
for max_freq in "${MAX_FREQ[@]}"; do
    {
        temp_dir=$(mktemp -d)

        cd "$temp_dir"
        python3 "$SCRIPT" \
            --minfreq "${MIN_FREQ}" \
            --maxfreq "${max_freq}" \
            --numwords "${NUM_WORDS}" \
            --index arxiv_abs

        cp vocabulary.txt "${RESULTS}/vocabulary_${MIN_FREQ}_${max_freq}_${NUM_WORDS}.txt"
        cp documents.txt "${RESULTS}/documents_${MIN_FREQ}_${max_freq}_${NUM_WORDS}.txt"
    } &
done

wait
