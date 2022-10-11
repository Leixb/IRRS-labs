#!/usr/bin/env python3

import argparse
import sys
from functools import partial
from heapq import nlargest
from itertools import chain
from multiprocessing import Pool, cpu_count
from typing import List, Tuple

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl import Q, Search
from TFIDFViewer import cosine_similarity, search_file_by_path, toTFIDF


# Theoretically, Elasticsearch client should be thread-safe, but sometimes
# it throws an exception. So we create a new client for each worker instead.
def worker_init(*args, **kwargs):
    global _client
    _client = Elasticsearch(*args, **kwargs)


class Slicer:
    def __init__(
        self, index: str, n: int, tfw_orig, slices: int, ignore_paths: List[str]
    ):
        self.index = index
        self.n = n
        self.slices = slices
        self.tfw_orig = tfw_orig
        self.ignore_paths = ignore_paths

    def process_slice(self, slice_no: int) -> List[Tuple[float, str]]:
        global client
        sc = (
            Search(using=_client, index=self.index)
            .query("match_all")
            .extra(slice={"id": slice_no, "max": self.slices})
            .scan()
        )

        def filter_path(hit):
            for path in self.ignore_paths:
                if hit.path.startswith(path):
                    return False
            return True

        doc_ids = filter(filter_path, sc)

        doc_ids = map(lambda f: f.meta.id, doc_ids)
        scores = map(
            lambda doc: (
                cosine_similarity(self.tfw_orig, toTFIDF(_client, self.index, doc)),
                doc,
            ),
            doc_ids,
        )

        return nlargest(self.n, scores)


def main(index: str, path: str, n: int, ignore_paths: List[str], slices: int):
    client = Elasticsearch(timeout=1000)

    print(ignore_paths)

    doc_original = search_file_by_path(client, index, path)

    tfidf = partial(toTFIDF, client, index)

    tfw_orig = list(tfidf(doc_original))

    print("Original file:", doc_original, path, sep="\t", file=sys.stderr)
    keywords = [x[0] for x in nlargest(10, tfw_orig, key=lambda x: x[1])]
    print("Keywords:", ", ".join(keywords))

    slicer = Slicer(index, n, tfw_orig, slices, ignore_paths)

    with Pool(slices, initializer=worker_init) as p:
        results = p.map(slicer.process_slice, range(slices))

    results = nlargest(n, chain(*results), key=lambda x: x[0])

    for score, docid in results:
        print(score, docid, end="\t", sep="\t")
        # get the document
        doc = client.get(index=index, id=docid)
        print(doc["_source"]["path"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search for a file using its path")
    parser.add_argument("--index", type=str, help="index to search in")
    parser.add_argument("path", type=str, help="path of the file to search")
    parser.add_argument(
        "--ignore-paths",
        type=str,
        help="ignore paths containing this strings",
        nargs="+",
        default=[],
    )
    parser.add_argument(
        "--nproc",
        type=int,
        help="Number of processes to use",
        default=cpu_count() - 1,
    )
    parser.add_argument("-n", type=int, default=10, help="number of results to return")
    args = parser.parse_args()

    try:
        main(
            args.index,
            args.path,
            args.n,
            ignore_paths=args.ignore_paths,
            slices=args.nproc,
        )
    except NotFoundError:
        print("Not found", file=sys.stderr)
        sys.exit(1)
