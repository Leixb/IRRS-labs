#!/usr/bin/env python3
"""
.. module:: ExtractData

ExtractData
*************

:Description: ExtractData

    Generates vector data representation with the most frequent words

:Authors: bejar


:Version:

:Created on: 12/07/2017 8:20

"""

import argparse
from collections import Counter
from itertools import dropwhile, islice, takewhile
from typing import Dict, Set

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from elasticsearch.helpers import scan

__author__ = "bejar"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", default=None, required=True, help="Index to search")
    parser.add_argument(
        "--minfreq",
        default=0.0,
        type=float,
        required=False,
        help="Minimum word frequency",
    )
    parser.add_argument(
        "--maxfreq",
        default=1.0,
        type=float,
        required=False,
        help="Maximum word frequency",
    )
    parser.add_argument(
        "--numwords", default=None, type=int, required=False, help="Number of words"
    )

    args = parser.parse_args()

    index = args.index
    minfreq = args.minfreq
    maxfreq = args.maxfreq
    numwords = args.numwords

    try:
        client = Elasticsearch(timeout=1000)

        voc: Counter[str] = Counter()
        docterms: Dict[str, Set[str]] = {}  # document vocabulary

        print("Querying all documents ...")
        sc = scan(client, index=index, query={"query": {"match_all": {}}})
        print("Generating vocabulary frequencies ...")

        for s in sc:
            docpath = s["_source"]["path"]
            docterms[docpath] = set()  # use a set for efficient operations
            tv = client.termvectors(
                index=index, doc_type="document", id=s["_id"], fields=["text"]
            )
            if "text" in tv["term_vectors"]:
                terms = tv["term_vectors"]["text"]["terms"]
                docterms[docpath].update(terms.keys())
                voc.update(terms.keys())

        fmax = voc.most_common(1)[0][1]

        actual_max_freq = fmax * maxfreq
        actual_min_freq = fmax * minfreq

        a = dropwhile(lambda x: x[1] > actual_max_freq, voc.most_common(None))
        b = takewhile(lambda x: x[1] > actual_min_freq, a)

        if numwords is None:
            lwords = [x[0] for x in b]
        else:
            lwords = [x[0] for x in islice(b, numwords)]

        lwords = sorted(lwords)

        print("Computing binary term vectors ...")
        for doc in docterms:
            docterms[doc] = docterms[doc].intersection(lwords)

        print("Saving data ...")
        with open("vocabulary.txt", "w") as f:
            for p in lwords:
                f.write(
                    p.encode("ascii", "replace").decode() + " " + str(voc[p]) + "\n"
                )

        with open("documents.txt", "w") as f:
            for doc in docterms:
                # get two last elements of path
                docname = "/".join(doc.split("/")[-2:])
                docvec = ""
                for v in lwords:
                    docvec += (" " + v) if v in docterms[doc] else ""
                if docvec:  # writes the document if there are words from the vocabulary
                    f.write(
                        docname
                        + ":"
                        + docvec.encode("ascii", "replace").decode()
                        + "\n"
                    )

    except NotFoundError:
        print(f"Index {index} does not exist")
