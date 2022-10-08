#!/usr/bin/env bash

# Script to compute the top 10 most frequent words in collection
# of text files using different elasticsearch filters
#
# It tries all the possible combinations

set -eo pipefail

FILTERS=(lowercase asciifolding stop porter_stem kstem snowball)
TOKEN=${TOKEN:-standard}

DATA="${DATA:-./data}"
FOLDER="$1"

if [ $# -eq 0 ]; then
    echo "Usage: $0 <folder> [filter1 filter2 ...]" >&2
    FOLDER="${DATA}/20_newsgroups"
    echo "Using default folder: $FOLDER" >&2
fi

if [ ! -d "$FOLDER" ]; then
    echo "Folder $FOLDER does not exist" >&2
    exit 1
fi

# Number of top terms to show
N=${N:-10}

shift || true

if [ $# -gt 0 ]; then
    FILTERS=("$@")
fi

echo "Using filters: ${FILTERS[*]}" >&2

combinations() {
    # print all possible combinations of the values given
    # using bitwise operations
    local -r values=("$@")
    local -r n="${#values[@]}"
    local -r bits="$((1 << n))"
    for i in $(seq 0 "$((bits - 1))"); do
        for j in $(seq 0 "$((n - 1))"); do
            if [ $((i & (1 << j))) -ne 0 ]; then
                echo -n "${values[j]} "
            fi
        done
        echo "" # newline
    done | sed 's/ $//'
}

csv_header() {
    for i in $(seq 1 "$N"); do
        echo -n "freq_$i;term_$i;"
    done
    echo "unique;total;source;filters"
}

extract_top() {
    filter=("$@")
    echo "Extracting top $N terms for: ${filter[*]}." >&2
    filters_join="${filter[*]}"
    filters_join="${filters_join// /,}"
    index_name="$(basename "$FOLDER");${filters_join}"
    index_name="${index_name//,/-}"
    ./IndexFilesPreprocess_par.py --index "$index_name" --path "$FOLDER" --token "$TOKEN" --filter "${filter[@]}" >/dev/null 2>/dev/null
    ./CountWords_par.py --index "$index_name" --top "$N" |
        awk -v N="$N" -F',? ' 'BEGIN {ORS=";"} NR <= N { print $1 ";" $2 } END { print $1 ";" $2 }'
    echo "$index_name"
}

csv_header
combinations "${FILTERS[@]}" | while read -r filter; do
    # shellcheck disable=SC2086
    extract_top $filter
done
