#!/usr/bin/env python3

import argparse
import pickle as pkl
import sys
from collections import Counter
from functools import partial, reduce
from multiprocessing import Pool, cpu_count
from typing import Dict, Iterable, Set, Tuple

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl import Search

DocTerms = Dict[str, Set[str]]
client = Elasticsearch(timeout=1000)


def process_slice(
    slice_no: int, index: str, max_slices
) -> Tuple[Counter[str], DocTerms]:
    se = (
        Search(using=client, index=index)
        .query("match_all")
        .extra(slice={"id": slice_no, "max": max_slices})
    )

    voc: Counter[str] = Counter()
    docterms: DocTerms = {}  # document vocabulary

    for s in se.scan():
        docpath = s.path
        docterms[docpath] = set()  # use a set for efficient operations
        tv = client.termvectors(
            index=index, doc_type="document", id=s.meta.id, fields=["text"]
        )
        if "text" in tv["term_vectors"]:
            terms = tv["term_vectors"]["text"]["terms"]
            docterms[docpath].update(terms.keys())
            voc.update(terms.keys())

    return voc, docterms


def join_tuples(
    t1: Tuple[Counter[str], DocTerms], t2: Tuple[Counter[str], DocTerms]
) -> Tuple[Counter[str], DocTerms]:
    voc1, docterms1 = t1
    voc2, docterms2 = t2

    return voc1 + voc2, {**docterms1, **docterms2}


def merge_slices(
    voc_doc: Iterable[Tuple[Counter[str], DocTerms]]
) -> Tuple[Counter[str], DocTerms]:
    return reduce(join_tuples, voc_doc)


def extract(index: str, output: str) -> Tuple[Counter[str], DocTerms]:
    print("Querying all documents ...", file=sys.stderr)
    n_threads = cpu_count() - 2
    fn = partial(process_slice, index=args.index, max_slices=n_threads)

    try:
        with Pool(n_threads) as p:
            voc_doc = p.map(fn, range(n_threads))
    except NotFoundError:
        print(f"Index {args.index} does not exist", file=sys.stderr)
        exit(1)

    return merge_slices(voc_doc)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", default=None, required=True, help="Index to search")
    parser.add_argument("--output", default=None, required=False, help="Output pickle")

    args = parser.parse_args()

    if args.output is None:
        args.output = args.index + ".pkl"

    voc, docterms = extract(args.index, args.output)

    # save pickle
    print("Saving pickle ...", file=sys.stderr)
    with open(f"{args.output}", "wb") as f:
        pkl.dump((voc, docterms), f)

    print("Saving frequencies ...", file=sys.stderr)
    with open(f"{args.index}.freq", "w") as f:
        f.write("term,freq\n")
        for w, c in voc.most_common():
            f.write(f"{w},{c}\n")
