#!/usr/bin/env python3

# Parallel implementation of CountWords.py

import argparse
from collections import Counter
from functools import reduce
from multiprocessing import Pool, cpu_count

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError, TransportError
from elasticsearch_dsl import Search


def process_slice(slice_no) -> Counter[str]:
    se = (
        Search(using=client, index=args.index)
        .query("match_all")
        .extra(slice={"id": slice_no, "max": SLICES})
    )
    sc = se.scan()

    counter: Counter = Counter()
    for s in sc:
        try:
            tv = client.termvectors(index=args.index, id=s.meta.id, fields=["text"])
            if "text" in tv["term_vectors"]:
                for t, ttv in tv["term_vectors"]["text"]["terms"].items():
                    counter[t] += ttv["term_freq"]
        except TransportError:
            pass

    return counter


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", default="twitter", help="Index name")
    parser.add_argument("--all", action="store_true", help="Dump all the words")
    parser.add_argument(
        "--top", type=int, default=10, help="Number of top words to print"
    )
    parser.add_argument(
        "--alpha", action="store_true", default=False, help="Sort words alphabetically"
    )
    args = parser.parse_args()

    client = Elasticsearch(timeout=1000)

    SLICES = cpu_count() - 1
    print("Using {} slices".format(SLICES))

    try:
        with Pool(SLICES) as pool:
            results = pool.map(process_slice, range(SLICES))
    except NotFoundError:
        print("Index does not exist")
        exit(1)

    voc = reduce(lambda a, b: a + b, results)

    if args.all:
        lpal = [(k.encode("utf-8", "ignore"), v) for k, v in voc.items()]

        for pal, cnt in sorted(lpal, key=lambda x: x[0 if args.alpha else 1]):
            print(f'{cnt}, {pal.decode("utf-8")}')

    elif args.top > 0:
        for w, c in voc.most_common(args.top):
            print(f"{c}, {w}")
    print("--------------------")
    print(f"{len(voc)} Unique Words")
    print(f"{voc.total()} Words")
