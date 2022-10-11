#!/usr/bin/env python3

import argparse
import sys
from functools import partial
from heapq import nlargest
from itertools import chain
from multiprocessing import Pool
from typing import Generator, Iterable

import numpy as np
import numpy.typing as npt
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl import Q, Search
from TFIDFViewer import cosine_similarity, search_file_by_path, toTFIDF

cnt = 0


def get_file_id(f):
    global cnt
    cnt += 1
    print(cnt, end="\r", file=sys.stderr)
    return f.meta.id


def all_file_ids(client, index):
    s = Search(using=client, index=index)
    q = Q()
    s = s.query(q)
    yield from map(get_file_id, s.scan())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search for a file using its path")
    parser.add_argument("path", type=str, help="path of the file to search")
    parser.add_argument("index", type=str, help="index to search in")
    parser.add_argument("-n", type=int, default=10, help="number of results to return")
    args = parser.parse_args()

    top_n = partial(nlargest, n=args.n)

    global client
    client = Elasticsearch(timeout=1000)

    doc_original = search_file_by_path(client, args.index, args.path)

    tfidf = partial(toTFIDF, client, args.index)

    tfw_orig = list(tfidf(doc_original))

    print("Original file:", args.path, file=sys.stderr)
    keywords = [x[0] for x in nlargest(10, tfw_orig, key=lambda x: x[1])]
    print("Keywords:", ", ".join(keywords))

    doc_ids = all_file_ids(client, args.index)

    sim = partial(cosine_similarity, tfw_orig)
    results = nlargest(args.n, map(lambda doc: (sim(tfidf(doc)), doc), doc_ids))

    for score, docid in results:
        print(score, docid, end="\t", sep="\t")
        # get the document
        doc = client.get(index=args.index, id=docid)
        print(doc["_source"]["path"])
