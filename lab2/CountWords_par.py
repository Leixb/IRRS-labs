#!/usr/bin/env python3

# Parallel implementation of CountWords.py

import argparse
import sys
from collections import Counter
from functools import partial, reduce
from multiprocessing import Pool, cpu_count
from typing import Iterable

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError, TransportError
from elasticsearch_dsl import Search

__client = None


class EsCounter:
    def __init__(self, client: Elasticsearch, slices: int):
        self.slices = slices

        global __client
        __client = client

    def process_slice(self, slice_no: int, index: str) -> Counter[str]:
        se = (
            Search(using=__client, index=index)
            .query("match_all")
            .extra(slice={"id": slice_no, "max": self.slices})
        )
        sc = se.scan()

        counter: Counter = Counter()
        for s in sc:
            try:
                tv = __client.termvectors(index=index, id=s.meta.id, fields=["text"])
                if "text" in tv["term_vectors"]:
                    for t, ttv in tv["term_vectors"]["text"]["terms"].items():
                        counter[t] += ttv["term_freq"]
            except TransportError:
                print("TransportError", file=sys.stderr)
                pass

        return counter


def join_counters(counters: Iterable[Counter]) -> Counter:
    return reduce(lambda x, y: x + y, counters)


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

    n_slices = cpu_count() - 1
    es_counter = EsCounter(client, slices=n_slices)

    print("Using {} slices".format(es_counter.slices), file=sys.stderr)

    slice_processor = partial(es_counter.process_slice, index=args.index)
    try:
        with Pool(n_slices) as pool:
            voc = join_counters(pool.map(slice_processor, range(n_slices)))
    except NotFoundError:
        print("Index does not exist", file=sys.stderr)
        exit(1)

    if args.all:
        lpal = [(k.encode("utf-8", "ignore"), v) for k, v in voc.items()]

        for pal, cnt in sorted(lpal, key=lambda x: x[0 if args.alpha else 1]):
            print(f'{cnt}, {pal.decode("utf-8")}')

    elif args.top > 0:
        for w, c in voc.most_common(args.top):
            print(f"{c}, {w}")
    print("--------------------")
    print(f"{len(voc)}, {voc.total()}")
    # print(f" Words")
