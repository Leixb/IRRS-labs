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
import sys
from multiprocessing import cpu_count
from typing import Generator, Iterable, List, Union

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from elasticsearch.helpers import parallel_bulk
from elasticsearch_dsl import Index, analyzer, tokenizer


class Indexer:
    def __init__(
        self,
        client: Elasticsearch = None,
        nprocs: int = max(cpu_count() - 2, 2),
    ):
        self.client = client if client else Elasticsearch(timeout=1000)
        self.nprocs = nprocs

    def index(
        self,
        index_name: str,
        files: Iterable[str],
        filter=Union[List[str], str],
        token: str = "standard",
    ) -> int:

        self.init_index(index_name, token, filter)

        return self.__process(build_operations(files, index_name))

    def __process(self, operations: Iterable[dict]) -> int:
        count = 0
        for success, info in parallel_bulk(
            self.client, operations, thread_count=self.nprocs
        ):
            if not success:
                print("Doc failed...")
            count += 1
            if count % 500 == 0:
                print("Indexed:", count, end="\r", file=sys.stderr)
        return count

    def init_index(
        self, index: str, token: str, filter: Union[List[str], str]
    ) -> Index:
        if isinstance(filter, str):
            filter = filter.split()

        my_analyzer = analyzer(
            "default",
            type="custom",
            tokenizer=tokenizer(token),
            filter=filter,
        )

        try:
            # Drop index if it exists
            ind = Index(index, using=self.client)
            ind.delete()
        except NotFoundError:
            pass
        # then create it
        ind.settings(number_of_shards=1)
        ind.create()
        ind = Index(index, using=self.client)

        # configure default analyzer
        ind.close()  # index must be closed for configuring analyzer
        ind.analyzer(my_analyzer)

        # configure the path field so it is not tokenized and we can do exact match search
        self.client.indices.put_mapping(
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

        return ind


def build_operations(files: Iterable[str], index: str) -> Generator[dict, None, None]:
    for file in files:
        with codecs.open(file, "r", encoding="iso-8859-1") as f:
            text = f.read()
            yield {"_op_type": "index", "_index": index, "path": file, "text": text}


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


__FILTERS__ = [
    "lowercase",
    "asciifolding",
    "stop",
    # "stemmer", # Same as porter_stem for english
    "porter_stem",
    "kstem",
    "snowball",
]


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
        choices=__FILTERS__,
        nargs="*",
        help="Text filters",
    )

    args = parser.parse_args()

    Indexer().index(
        args.index,
        files=generate_files_list(args.path),
        filter=args.filter,
        token=args.token,
    )
