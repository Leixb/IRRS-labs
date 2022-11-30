#!/usr/bin/env python3
"""
.. module:: MRKmeansDef

MRKmeansDef
*************

:Description: MRKmeansDef



:Authors: bejar


:Version:

:Created on: 17/07/2017 7:42

"""

from collections import Counter
from typing import Dict, Generator, List, Tuple

from mrjob.job import MRJob
from mrjob.step import MRStep

__author__ = "bejar"

# A prototype is a list of (word, probability) pairs:
Prototype = List[Tuple[str, float]]
Assignment = List[str]  # [doc1, doc2, ...]

# Key-Value of intermediate map-reduce step
Key = str  # Prototype ID
Value = Tuple[str, List[str]]  # DocID, [word1, word2, ...]


class MRKmeansStep(MRJob):

    prototypes: Dict[str, Prototype] = {}

    def jaccard(self, prot: Prototype, doc: List[str]) -> float:
        """
        Compute here the Jaccard similarity between  a prototype and a document
        prot should be a list of pairs (word, probability)
        doc should be a list of words
        Words must be alphabetically ordered

        The result should be always a value in the range [0,1]
        """

        i = 0
        j = 0
        inter = 0
        while i < len(prot) and j < len(doc):
            if prot[i][0] == doc[j]:
                inter += 1
                i += 1
                j += 1
            elif prot[i][0] < doc[j]:
                i += 1
            else:
                j += 1

        return inter / float(len(prot) + len(doc) - inter)

    def configure_args(self) -> None:
        """
        Additional configuration flag to get the prototypes files

        :return:
        """
        super(MRKmeansStep, self).configure_args()
        self.add_file_arg("--prot")

    def load_data(self) -> None:
        """
        Loads the current cluster prototypes

        :return:
        """
        with open(self.options.prot, "r") as f:
            for line in f:
                cluster, words = line.split(":")
                cp = []
                for word in words.split():
                    w, p = word.split("+")
                    cp.append((w, float(p)))
                self.prototypes[cluster] = cp

    def assign_prototype(
        self, _, line: str
    ) -> Generator[Tuple[Key, Value], None, None]:
        """
        This is the mapper it should compute the closest prototype to a document

        Words should be sorted alphabetically in the prototypes and the documents

        This function has to return at list of pairs (prototype_id, document words)

        You can add also more elements to the value element, for example the document_id
        """

        # Each line is a string docid:wor1 word2 ... wordn
        doc, words = line.split(":")
        lwords = words.split()

        #
        # Compute map here
        #
        prot_iter = iter(self.prototypes)

        best_prot = next(prot_iter)
        best_dist = self.jaccard(self.prototypes[best_prot], lwords)

        for prot in prot_iter:
            distance = self.jaccard(self.prototypes[prot], lwords)
            if distance < best_dist:
                best_prot = prot
                best_dist = distance

        yield best_prot, (doc, lwords)

    def aggregate_prototype(
        self, key: Key, values: List[Value]
    ) -> Generator[Tuple[Key, Tuple[Assignment, Prototype]], None, None]:
        """
        input is cluster and all the documents it has assigned
        Outputs should be at least a pair (cluster, new prototype)

        It should receive a list with all the words of the documents assigned for a cluster

        The value for each word has to be the frequency of the word divided by the number
        of documents assigned to the cluster

        Words are ordered alphabetically but you will have to use an efficient structure to
        compute the frequency of each word

        :param key:
        :param values:
        :return:
        """

        word_freq: Counter[str] = Counter()

        documents = []
        for doc, words in values:
            documents.append(doc)
            word_freq.update(words)

        num_docs = len(documents)

        # New prototype:
        prot = sorted(map(lambda x: (x[0], float(x[1]) / num_docs), word_freq.items()))

        yield key, (sorted(documents), prot)

    def steps(self) -> List[MRStep]:
        return [
            MRStep(
                mapper_init=self.load_data,
                mapper=self.assign_prototype,
                reducer=self.aggregate_prototype,
            )
        ]


if __name__ == "__main__":
    MRKmeansStep.run()
