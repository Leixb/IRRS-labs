#!/usr/bin/env bash

set -eo pipefail

DATA="${OUTPUT:-data}"

echo "min_freq,max_freq,n_words,voc_size,clusters,iterations,converged,total_time,iter_time"

# shellcheck disable=SC2016 # (we don't want to expand awk variables)
find "${DATA}" -name kmeans.log -exec echo -n {}, \; \
    -execdir sh -c "wc -l <vocabulary.txt | tr '\n' ," \; \
    -execdir sh -c "ls prototypes* | sort -V | tail -n 1 | xargs wc -l | cut -d' ' -f1 | tr '\n' ," \; \
    -exec awk 'BEGIN {con=0} $1 == "Time=" {C++; time+=$2} $2 == "converged" { con = 1 } END {print C "," con "," time "," time/C}' {} \; |
    sed 's#/kmeans.log##' | sed 's#^.*/##' | tr _ ,
