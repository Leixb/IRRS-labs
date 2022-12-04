#!/usr/bin/env bash

set -eo pipefail

DATA="${OUTPUT:-data}"
ITER="${ITER:-10}"

NWORDS="${NWORDS:-100}"
PROT="${PROT:-$DATA/arxiv_abs/${NWORDS}_0.01_0.02}"

REPEAT="${REPEAT:-10}"

for ncores in $(seq 1 "7"); do
    echo "Processing $PROT with $ncores cores"

    # Check if we have the initial prototype
    if [ ! -f "$PROT/prototype.txt" ]; then
        echo "$PROT/prototype.txt does not exist..." >&2
        echo "Did you run ./prototypes.sh?" >&2
        exit 1
    fi

    if [ -f "$PROT/kmeans_$ncores.log" ]; then
        echo "Found $PROT/kmeans_$ncores.log, skipping..."
        continue
    fi

    echo "Running $REPEAT times..."

    for i in $(seq 2 "$REPEAT"); do
        echo "REP $i"
        ./MRKmeans.py \
            --prot "$PROT/prototype.txt" \
            --ncores "$ncores" \
            --output "$PROT" \
            --iter "${ITER}" \
            --docs "$PROT/documents.txt"
    done | tee "$PROT/kmeans_$ncores.log"
done
