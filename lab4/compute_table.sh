#!/usr/bin/env bash

set -eo pipefail

DATA="${OUTPUT:-data}"

echo "min_freq,max_freq,n_words,voc_size,iterations,converged"

# shellcheck disable=SC2016 # (we don't want to expand awk variables)
find "${DATA}" -name kmeans.log -exec echo -n {}, \; \
    -execdir sh -c "wc -l vocabulary.txt | awk -v ORS= '{print \$1 \",\"}'" \; \
    -exec awk 'BEGIN {con=0} $1 == "Time=" {C++} $2 == "converged" { con = 1 } END {print C "," con }' {} \; |
    sed 's#/kmeans.log##' | sed 's#^.*/##' | tr _ ,
