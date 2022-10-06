#!/usr/bin/env python3

"""
.. module:: IndexFilesPreprocess

IndexFiles
******

:Description: IndexFilesPreprocess

    Indexes a set of files under the directory passed as a parameter (--path)
    in the index name passed as a parameter (--index)

    Add configuration of the default analizer: tokenizer  (--token) and filter (--filter)

    --filter must be always the last flag

    If the index exists it is dropped and created new

    Documentation for the analyzer configuration:

    https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis.html

:Authors:
    bejar

:Version:

:Date:  23/06/2017
"""

import argparse
import codecs
import os
from multiprocessing import cpu_count
from typing import Generator

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from elasticsearch.helpers import parallel_bulk
from elasticsearch_dsl import Index, analyzer, tokenizer


def generate_files_list(path) -> Generator[str, None, None]:
    """
    Generates a list of all the files inside a path
    :param path:
    :return:
    """
    if path[-1] == "/":
        path = path[:-1]

    for lf in os.walk(path):
        if lf[2]:
            for f in lf[2]:
                yield lf[0] + "/" + f


__author__ = "bejar"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True, default=None, help="Path to the files")
    parser.add_argument(
        "--index", required=True, default=None, help="Index for the files"
    )
    parser.add_argument(
        "--token",
        default="standard",
        choices=["standard", "whitespace", "classic", "letter"],
        help="Text tokenizer",
    )
    parser.add_argument(
        "--filter",
        default=["lowercase"],
        nargs=argparse.REMAINDER,
        help="Text filter: lowercase, "
        "asciifolding, stop, porter_stem, kstem, snowball",
    )

    args = parser.parse_args()

    path = args.path
    index = args.index

    # check if the filters are valid
    for f in args.filter:
        if f not in [
            "lowercase",
            "asciifolding",
            "stop",
            "stemmer",
            "porter_stem",
            "kstem",
            "snowball",
        ]:
            raise NameError(
                "Invalid filter must be a subset of: lowercase, asciifolding, stop, porter_stem, kstem, snowball"
            )

    # Reads all the documents in a directory tree and generates an index operation for each
    lfiles = generate_files_list(path)

    def build_operation(file: str) -> dict:
        with codecs.open(file, "r", encoding="iso-8859-1") as f:
            text = f.read()
            return {"_op_type": "index", "_index": index, "path": file, "text": text}

    ldocs = map(build_operation, lfiles)

    client = Elasticsearch(timeout=1000)

    # Tokenizers: whitespace classic standard letter
    my_analyzer = analyzer(
        "default", type="custom", tokenizer=tokenizer(args.token), filter=args.filter
    )

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

    # configure the path field so it is not tokenized and we can do exact match search
    client.indices.put_mapping(
        doc_type="document",
        index=index,
        include_type_name=True,
        body={
            "properties": {
                "path": {
                    "type": "keyword",
                }
            }
        },
    )

    ind.save()
    ind.open()
    print("Index settings=", ind.get_settings())
    # Bulk execution of elastic search operations (faster than executing all one by one)
    print("Indexing ...")

    for success, info in parallel_bulk(client, ldocs, thread_count=cpu_count() - 2):
        if not success:
            print("A document failed:", info)
