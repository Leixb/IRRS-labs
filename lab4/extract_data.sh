#!/usr/bin/env bash

set -eo pipefail

MAX_FREQ=(0.01 0.02 0.03 0.04 0.05 0.06 0.07 0.08 0.09 0.1)
MIN_FREQ=(0.0)
NUM_WORDS=(100 250)

DATA="${OUTPUT:-data}"
DATA="$(realpath "$DATA")"
mkdir -p "${DATA}"
export DATA

SCRIPT="$(realpath ./ExtractData.py)"
export SCRIPT

TEMP_DIR="$(mktemp -d)"
export TEMP_DIR

export INDEX="${INDEX:-arxiv_abs}"

cleanup() {
    rm -rf "${TEMP_DIR}"
}

trap cleanup EXIT

compute() {
    local min_freq="$1"
    local max_freq="$2"
    local num_words="$3"

    # check min < max
    if (($(echo "$min_freq > $max_freq" | bc -l))); then
        echo "Skipping: min_freq ($min_freq) > max_freq ($max_freq)"
        return
    fi

    local info="${min_freq}_${max_freq}_${num_words}"
    local output_dir="${DATA}/${info}"

    # skip if output dir exists
    if [[ -d ${output_dir} ]]; then
        echo "Skipping ${info} (${output_dir} exists)"
        return
    fi

    mkdir -p "${output_dir}"
    cd "${output_dir}"

    "${SCRIPT}" \
        --index "${INDEX}" \
        --minfreq "${min_freq}" \
        --maxfreq "${max_freq}" \
        --numwords "${num_words}" | tee "${output_dir}/generate.log"
}

export -f compute

parallel compute ::: "${MIN_FREQ[@]}" ::: "${MAX_FREQ[@]}" ::: "${NUM_WORDS[@]}"
