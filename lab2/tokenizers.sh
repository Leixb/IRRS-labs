#!/usr/bin/env bash

set -eo pipefail

TOKENS=(whitespace classic standard letter)

DATA="${DATA:-./data}"
FOLDER="$1"

if [ $# -eq 0 ]; then
    echo "Usage: $0 <folder> [tokenizer1] [tokenizer2] ..." >&2
    FOLDER="${DATA}/novels"
    echo "Using default folder: $FOLDER"
fi

if [ ! -d "$FOLDER" ]; then
    echo "Folder $FOLDER does not exist" >&2
    exit 1
fi

shift || true

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
