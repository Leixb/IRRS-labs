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
import pathlib
import pickle as pkl
from collections import Counter
from functools import partial
from itertools import dropwhile, islice, product, repeat, takewhile, tee
from multiprocessing import Pool, cpu_count
from typing import Dict, Iterable, List, Optional, Set, Tuple

DocTerms = Dict[str, Set[str]]


__author__ = "bejar"


def main(
    output: str,
    index: str,
    voc: Counter[str],
    docterms: DocTerms,
    numwords: List[int],
    minfreq: List[float],
    maxfreq: List[float],
    nproc: int = 2,
) -> None:

    fmax = voc.most_common(1)[0][1]

    # all combinations of numwords, minfreq, maxfreq:
    params = list(filter(lambda x: x[1] < x[2], product(numwords, minfreq, maxfreq)))
    n = len(params)

    print("Generating {} combinations of parameters".format(n))

    list_voc_iters = tee(voc.most_common(None), n)

    it_params = [
        (x, y) + z for x, y, z in zip(list_voc_iters, repeat(docterms), params)
    ]

    with Pool(nproc) as pool:
        pool.starmap(partial(run, output, index, fmax, voc), it_params)


def run(
    output: str,
    index: str,
    fmax: int,
    voc: Counter[str],
    voc_it: Iterable[Tuple[str, int]],
    docterms: DocTerms,
    numwords: int,
    minfreq: float,
    maxfreq: float,
) -> None:
    folder = pathlib.Path(f"{output}/{index}/{numwords}_{minfreq}_{maxfreq}")

    # skip if folder already exists:
    if folder.exists():
        print(f"Skipping {folder}")
        return

    folder.mkdir(parents=True, exist_ok=True)

    minf = int(minfreq * fmax)
    maxf = int(maxfreq * fmax)

    lwords, docterms = filter_freq(voc_it, docterms, numwords, minf, maxf)

    with open(folder.joinpath("stats.csv"), "w") as f:
        freq_last = voc[lwords[-1]] / float(fmax)
        print("minfreq,maxfreq,numwords,realminfreq,realnumwords", file=f)
        print(f"{minfreq},{maxfreq},{numwords},{freq_last},{len(lwords)}", file=f)

    with open(folder.joinpath("vocabulary.txt"), "w") as f:
        for w in lwords:
            f.write(w.encode("ascii", "replace").decode() + " " + str(voc[w]) + "\n")

    with open(folder.joinpath("documents.txt"), "w") as f:
        for doc in docterms:
            # get two last elements of path
            docname = "/".join(doc.split("/")[-2:])
            docvec = ""
            for v in lwords:
                docvec += (" " + v) if v in docterms[doc] else ""
            if docvec:  # writes the document if there are words from the vocabulary
                f.write(
                    docname + ":" + docvec.encode("ascii", "replace").decode() + "\n"
                )


def filter_freq(
    voc: Iterable[Tuple[str, int]],
    docterms: DocTerms,
    numwords: Optional[int],
    minf: int,
    maxf: int,
) -> Tuple[List[str], DocTerms]:

    docterms = docterms.copy()

    a = dropwhile(lambda x: x[1] > maxf, voc)
    b = takewhile(lambda x: x[1] >= minf, a)

    if numwords is None or numwords == 0:
        lwords = [x[0] for x in b]
    else:
        lwords = [x[0] for x in islice(b, numwords)]

    lwords = sorted(lwords)

    for doc in docterms:
        docterms[doc] = docterms[doc].intersection(lwords)

    return lwords, docterms


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", default=None, required=True, help="Index to search")
    parser.add_argument(
        "--minfreq",
        default=[0.0],
        nargs="+",
        type=float,
        required=False,
        help="Minimum word frequency",
    )
    parser.add_argument(
        "--maxfreq",
        default=[1.0],
        nargs="+",
        type=float,
        required=False,
        help="Maximum word frequency",
    )
    parser.add_argument("--input", default=None, required=False, help="Input pickle")
    parser.add_argument(
        "--numwords",
        default=[100],
        type=int,
        required=False,
        help="Number of words",
        nargs="+",
    )
    parser.add_argument(
        "--output", default="data", required=False, help="Output directory"
    )
    parser.add_argument(
        "--nproc",
        default=min(2, cpu_count() - 2),
        required=False,
        help="Number of processes",
    )

    args = parser.parse_args()

    index = args.index
    minfreq = args.minfreq
    maxfreq = args.maxfreq
    numwords = args.numwords

    if args.input is None:
        args.input = args.index + ".pkl"

    # read pickle
    with open(f"{args.input}", "rb") as f:
        voc, docterms = pkl.load(f)

    main(args.output, args.index, voc, docterms, numwords, minfreq, maxfreq)
