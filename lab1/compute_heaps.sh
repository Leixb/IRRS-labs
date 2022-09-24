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

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

INPUT="${1:-${SCRIPT_DIR}/data/novels}"
INPUT="$(realpath "$INPUT")"

N="${2:-50}"

export SEP="${SEP:-,}"


PARAMS="${PARAMS:-"-d --additional-suffix .txt"}"
export PARAMS="${PARAMS} -n l/${N}"

# Decrease N by 1 so seq works properly
export N=$((N-1))

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
export OUTPUT="$(realpath "$OUTPUT")"

cleanup() {
    if [ "$DO_CLEANUP" -eq 1 ]; then
        echo "Cleaning up... $OUTPUT" >&2
        rm -rf "$OUTPUT"
    else
        echo "Output folder: $OUTPUT" >&2
    fi
}

trap cleanup EXIT

split_file () {
    local file="$1"
    local name="$(basename "$file" .txt)"
    local curr_output="${OUTPUT}/${name}"
    mkdir -p "${curr_output}"
    cd "${curr_output}"
    split "${file}" ${PARAMS} #"${prefix}."
    echo "Split ${file} into ${curr_output}" >&2
    echo "${curr_output}"
}

process_splits () {
    local novel="$1"
    local name="$(basename "${novel}" .txt)"
    echo "Processing ${name} ..." >&2

    FILES_TO_PROCESS=()
    for i in $(seq -f "%02g" 00 "$N"); do
        FILES_TO_PROCESS+=("${novel}/x${i}.txt")
        process_split "${name}" "${i}" "${FILES_TO_PROCESS[@]}" &
    done
    wait
}

process_split () {
    local novel="$1"
    local split="$2"
    shift 2
    cat "$@" | count_uniq "${novel}" "${split}"
}

count_uniq () {
    # Separate all words into different lines
    # Convert to lowercase
    # Remove all non alphanumeric and return the count of unique words
    local novel="$1"
    # remove comma from novel (for csv)
    local novel="${novel//${SEP}/}"

    local split="$2"
    local tmpfile=$(mktemp)
    tr -s '[:punct:] ' '\n' | tr '[:upper:]' '[:lower:]' | tr -d -C '[:alpha:]\n' > "$tmpfile"

    local uniq="$(sort -u "$tmpfile" | wc -l)"
    local words="$(wc -w <"$tmpfile" )"

    echo "${novel}${SEP}${split}${SEP}${uniq}${SEP}${words}"
    rm "$tmpfile"
}

process_file() {
    local file="$1"
    local split_location=$(split_file "${file}")
    process_splits "${split_location}"
}

export -f process_file process_split count_uniq split_file process_splits

main () {
    if hash parallel 2>/dev/null ; then
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
