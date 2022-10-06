#!/usr/bin/env python3

import codecs
import os
import pathlib
from itertools import chain  # , islice
from multiprocessing import cpu_count
from typing import Dict, Generator, Iterable

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from elasticsearch.helpers import parallel_bulk
from elasticsearch_dsl import Index, analyzer, tokenizer


def file_list(paths: Iterable[pathlib.Path]) -> Generator[Dict, None, None]:

    print("Indexing files...")

    train = False

    for p in paths:
        train = not train

        rel = str(p.relative_to(folder))

        index = p.parent.name + ("_train" if train else "_test")

        with codecs.open(str(p), "r", encoding="iso-8859-1") as ftxt:
            text = "\n".join(ftxt.readlines())

        print("Indexing {}...".format(rel))

        yield {"_op_type": "index", "_index": index, "path": rel, "text": text}


def train_test(x: pathlib.Path) -> Generator[str, None, None]:
    yield x.name + "_train"
    yield x.name + "_test"


def init_index(index: str) -> None:
    try:
        # Drop index if it exists
        ind = Index(index, using=client)
        ind.delete()
    except NotFoundError:
        pass
    # then create it
    ind.settings(number_of_shards=1)
    ind.create()
    ind = Index(index, using=client)

    # configure default analyzer
    ind.close()  # index must be closed for configuring analyzer
    ind.analyzer(my_analyzer)

    print("Index {} created".format(index))


client = Elasticsearch(timeout=1000)

my_analyzer = analyzer(
    "default",
    type="custom",
    tokenizer=tokenizer("standard"),
    filter="lowercase stop kstem",
)


folder = pathlib.Path(os.environ["DATA"] or "data")
folder = folder.joinpath("20_newsgroups")

# Build elastic search action generator
newsgroups = folder.iterdir()
file_iter = chain.from_iterable(map(lambda x: x.iterdir(), newsgroups))

# Create indices
map(init_index, chain.from_iterable(map(train_test, newsgroups)))

# Bulk index
for success, info in parallel_bulk(
    client, file_list(file_iter), thread_count=cpu_count() - 2
):
    if not success:
        print("A document failed:", info)
