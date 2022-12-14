#!/usr/bin/env bash

tr ' :' '\n' <"$1" |
    awk '$1 ~ /^CLASS/ { class = $1; } {if ($1 != class) print class, $1; }' |
    sed 's#/[0-9]*$##' |
    sort |
    uniq -c |
    sed 's/CLASS//' |
    awk '{print $2 "." $1, $3}' |
    sort -V |
    sed 's/\./ /' |
    tr ' ' '\t' |
    awk 'BEGIN {class=0} $1 != class {class = $1; print "" } {print $0}' |
    sed 's/\.updates.*$//'
