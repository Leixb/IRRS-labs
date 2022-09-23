#!/usr/bin/env bash

count_uniq () {
    # Separate all words into different lines
    # Convert to lowercase
    # Remove all non alphanumeric and return the count of unique words
    tmpfile=$(mktemp)
    tr -s '[:punct:] ' '\n' | tr '[:upper:]' '[:lower:]' | tr -d -C '[:alpha:]\n' > "$tmpfile"

    UNIQ="$(sort -u "$tmpfile" | wc -l)"
    WORDS="$(wc -w <"$tmpfile" )"

    echo -e "$UNIQ\t$WORDS"
}

FOLDER="${FOLDER:-./novels_symfarm}"

for novel in "$FOLDER"/*; do
    for subfolder in "$novel"/*; do
        novel=$(basename "$novel")
        n=$(basename "$subfolder")
        echo -e "$novel\t$n\t$(cat "$subfolder"/*.txt | count_uniq)"
    done
done
