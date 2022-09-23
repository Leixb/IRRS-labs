#!/usr/bin/env bash

set -eo pipefail

N="${N:-50}"
N=$((N-1))

INPUT="${INPUT:-./novels}"

FOLDER="${FOLDER:-${INPUT}_split}"
FOLDER="$(realpath "$FOLDER")"

OUTPUT="${OUTPUT:-${INPUT}_symfarm}"
OUTPUT="$(realpath "$OUTPUT")"

for novel in "${FOLDER}"/*/; do
    name=$(basename "${novel}")
    echo "Processing ${name} ..."

    for i in $(seq 0 "$i"); do
        curr_out="${OUTPUT}/${name}/${i}"
        mkdir -p "${curr_out}"
        cd "${curr_out}"
        for j in $(seq -f "%02g" 00 "$i"); do
            target="$(realpath --relative-to="${curr_out}" "${novel}/x${j}.txt")"
            ln -s "${target}" .
        done
    done
done
