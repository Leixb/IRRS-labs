#!/usr/bin/env python3

import argparse
import sys
from functools import partial
from heapq import nlargest
from itertools import chain
from multiprocessing import Pool, cpu_count
from time import sleep
from typing import Callable, Generator, Iterable, Tuple

import numpy as np
import numpy.typing as npt
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl import Q, Search
from TFIDFViewer import cosine_similarity, search_file_by_path, toTFIDF

cnt = 0


def get_file_id(f):
    return f.meta.id


def all_file_ids(client, index):
    s = Search(using=client, index=index)
    q = Q()
    s = s.query(q)
    yield from map(get_file_id, s.scan())


def worker_init(*args, **kwargs):
    global _client
    _client = Elasticsearch(*args, **kwargs)


class Slicer:
    def __init__(self, index: str, n: int, tfw_orig, slices: int):
        self.index = index
        self.n = n
        self.slices = slices
        self.tfw_orig = tfw_orig

    def process_slice(self, slice_no: int) -> Iterable[Tuple[float, str]]:
        global client
        sc = (
            Search(using=_client, index=self.index)
            .query("match_all")
            .extra(slice={"id": slice_no, "max": self.slices})
            .scan()
        )

        doc_ids = map(get_file_id, sc)
        scores = map(
            lambda doc: (
                cosine_similarity(self.tfw_orig, toTFIDF(_client, self.index, doc)),
                doc,
            ),
            doc_ids,
        )

        return nlargest(self.n, scores)


def main(index: str, path: str, n: int):
    client = Elasticsearch(timeout=1000)

    doc_original = search_file_by_path(client, index, path)

    tfidf = partial(toTFIDF, client, index)

    tfw_orig = list(tfidf(doc_original))

    print("Original file:", path, file=sys.stderr)
    keywords = [x[0] for x in nlargest(10, tfw_orig, key=lambda x: x[1])]
    print("Keywords:", ", ".join(keywords))

    SLICES = cpu_count() - 1

    slicer = Slicer(index, n, tfw_orig, SLICES)

    with Pool(SLICES, initializer=worker_init) as p:
        results = p.map(slicer.process_slice, range(SLICES))

    results = nlargest(n, chain(*results), key=lambda x: x[0])

    for score, docid in results:
        print(score, docid, end="\t", sep="\t")
        # get the document
        doc = client.get(index=index, id=docid)
        print(doc["_source"]["path"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search for a file using its path")
    parser.add_argument("path", type=str, help="path of the file to search")
    parser.add_argument("index", type=str, help="index to search in")
    parser.add_argument("-n", type=int, default=10, help="number of results to return")
    args = parser.parse_args()

    main(args.index, args.path, args.n)
