#!/usr/bin/env bash

set -e

TOKENS=(whitespace classic standard letter)

if [ $# -ne 1 ]; then
    echo "Usage: $0 <input folder> [tokenizer1] [tokenizer2] ..."
    exit 1
fi

FOLDER="$1"
shift

if [ $# -ne 0 ]; then
    TOKENS=("$@")
fi

base="$(basename "$FOLDER")"

SEP=${SEP:-,}

echo "collection${SEP}token${SEP}words"
for token in "${TOKENS[@]}"; do
    index="$base-$token"
    ./IndexFilesPreprocess.py --index "$index" --path "$FOLDER" --token "$token" >/dev/null 2>&1
    words="$(./CountWords.py --index "$index" 2>/dev/null | tail -n 1 | cut -d ' ' -f 1)"
    echo "${base}${SEP}${token}${SEP}${words}"
done
