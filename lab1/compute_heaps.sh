#!/usr/bin/env bash

# Script to split files into chunks and compute
# the cummulative number of words and unique words
#
# Usage: ./compute_heaps.sh <folder> <chunk_size>
#
# Example: ./compute_heaps.sh data/novels 50
#
# Other options can be ajusted thought environment variables
# (see below)

set -eo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

DATA="${DATA:-${SCRIPT_DIR}/data}"
INPUT="${1:-${DATA}/novels}"
INPUT="$(realpath "$INPUT")"

if [ ! -d "${INPUT}" ]; then
    echo "Input folder does not exist: ${INPUT}" >&2
    exit 1
fi

N="${2:-50}"

export SEP="${SEP:-,}"

PARAMS="${PARAMS:-"-d --additional-suffix .txt"}"
PARAMS="${PARAMS} -n l/${N}"
IFS=" " read -r -a PARAMS <<<"${PARAMS}"
export PARAMS

# Decrease N by 1 so seq works properly
export N=$((N - 1))

# Delete output folder only if the user has not specified one
DO_CLEANUP=1
if [ -n "$OUTPUT" ]; then
    DO_CLEANUP=0
fi

# Use ramdisk if available (disable with NO_RAMDISK=1)
if [ -d /dev/shm ] && [ -z "$NO_RAMDISK" ]; then
    export TMPDIR=/dev/shm
fi

OUTPUT="${OUTPUT:-$(mktemp -d)}"
OUTPUT="$(realpath "$OUTPUT")"
export OUTPUT

cleanup() {
    if [ "$DO_CLEANUP" -eq 1 ]; then
        echo "Cleaning up... $OUTPUT" >&2
        rm -rf "$OUTPUT"
    else
        echo "Output folder: $OUTPUT" >&2
    fi
}

trap cleanup EXIT

split_file() {
    local -r file="$1"
    local -r name="$(basename "$file" .txt)"
    local -r curr_output="${OUTPUT}/${name}"
    mkdir -p "${curr_output}"
    cd "${curr_output}"
    split "${file}" "${PARAMS[@]}"
    echo "Split ${file} into ${curr_output}" >&2
    echo "${curr_output}"
}

process_splits() {
    local -r novel="$1"
    local -r name="$(basename "${novel}" .txt)"
    echo "Processing ${name} ..." >&2

    FILES_TO_PROCESS=()
    for i in $(seq -f "%02g" 00 "$N"); do
        FILES_TO_PROCESS+=("${novel}/x${i}.txt")
        process_split "${name}" "${i}" "${FILES_TO_PROCESS[@]}" &
    done
    wait
}

process_split() {
    local -r novel="$1"
    local -r split="$2"
    shift 2
    cat "$@" | count_uniq "${novel}" "${split}"
}

count_uniq() {
    # Separate all words into different lines
    # Convert to lowercase
    # Remove all non alphanumeric and return the count of unique words
    local novel="$1"
    # remove comma from novel (for csv)
    local -r novel="${novel//${SEP}/}"

    local -r split="$2"
    local -r tmpfile=$(mktemp)
    tr -s '[:punct:] ' '\n' | tr '[:upper:]' '[:lower:]' | tr -d -C '[:alpha:]\n' >"$tmpfile"

    local -r uniq="$(sort -u "$tmpfile" | wc -l)"
    local -r words="$(wc -w <"$tmpfile")"

    echo "${novel}${SEP}${split}${SEP}${uniq}${SEP}${words}"
    rm "$tmpfile"
}

process_file() {
    local -r file="$1"
    local -r split_location=$(split_file "${file}")
    process_splits "${split_location}"
}

export -f process_file process_split count_uniq split_file process_splits

main() {
    if hash parallel 2>/dev/null; then
        # If GNU parallel is available, use it to process files in parallel
        echo "Using GNU parallel" >&2
        echo "novel${SEP}split${SEP}unique${SEP}words" # csv header
        parallel process_file ::: "${INPUT}"/*.txt
    else
        for file in "${INPUT}"/*.txt; do
            # Uncomment & to process files in parallel
            # This may cause issues if you have a lot of files
            process_file "${file}" # &
        done
        wait
    fi
}

main "$@"
