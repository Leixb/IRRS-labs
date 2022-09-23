#!/usr/bin/env bash

set -eo pipefail

N="${N:-50}"

INPUT="${INPUT:-./novels}"
INPUT="$(realpath "$INPUT")"

OUTPUT="${OUTPUT:-${INPUT}_split}"
OUTPUT="$(realpath "$OUTPUT")"
mkdir -p "$OUTPUT"

PARAMS="${PARAMS:-"-d --additional-suffix .txt"}"
PARAMS="${PARAMS} -n l/${N}"

for file in "${INPUT}"/*.txt; do
    prefix="$(basename "${file}" .txt)"
    curr_output="${OUTPUT}/${prefix}"
    mkdir -p "${curr_output}"
    cd "${curr_output}"
    split "${file}" ${PARAMS} #"${prefix}."
    echo "Split ${file} into ${curr_output}"
done
