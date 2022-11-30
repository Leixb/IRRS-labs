#!/usr/bin/env bash

set -eo pipefail

export NCLUST=${NCLUST:-10}

DATA="${OUTPUT:-data}"

generate_prototypes() {
    folder="$1"
    echo "Generating prototypes for $folder"
    ./GeneratePrototypes.py \
        --data "$folder/documents.txt" \
        --output "$folder/prototype.txt" \
        --nclust "$NCLUST" | tee "$folder/prototypes.log"
}

export -f generate_prototypes

parallel generate_prototypes ::: "${DATA}/"*/
