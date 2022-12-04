#!/usr/bin/env bash

set -eo pipefail

DATA="${OUTPUT:-data}"
NCORES="${NCORES:-6}"
ITER="${ITER:-10}"

for prot in "${DATA}/"*/; do
    echo "Processing $prot"

    # Check if we have the initial prototype
    if [ ! -f "$prot/prototype.txt" ]; then
        echo "$prot/prototype.txt does not exist..." >&2
        echo "Did you run ./prototypes.sh?" >&2
        exit 1
    fi

    if [ -f "$prot/kmeans.log" ]; then
        echo "Found $prot/kmeans.log, skipping..."
        continue
    fi

    ./MRKmeans.py \
        --prot "$prot/prototype.txt" \
        --ncores "$NCORES" \
        --output "$prot" \
        --iter "${ITER}" \
        --docs "$prot/documents.txt" | tee "$prot/kmeans.log"
done
