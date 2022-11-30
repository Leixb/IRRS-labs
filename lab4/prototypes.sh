#!/usr/bin/env bash

set -eo pipefail

NCLUST=${NCLUST:-10}

# for i in ./results/documents_0.0_0.1_250.txt;
for i in ./results/documents*; do

    base="$(basename "$i" .txt)"
    prefix="${base%_*}"

    outdir="prototypes/${prefix}"
    mkdir -p "$outdir"

    cp "$i" "$outdir/documents.txt"

    ./GeneratePrototypes.py --data "$i" --output "$outdir/prototype.txt" --nclust "$NCLUST"

done

for prot in ./prototypes/*; do
    echo "Processing $prot"
    ./MRKmeans.py \
        --prot "prototype.txt" \
        --ncores 10 \
        --output "$prot" \
        --docs "$prot/documents.txt"
done
