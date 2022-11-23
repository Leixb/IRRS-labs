#!/usr/bin/env python3
"""
WordCountMR
"""
import re

from mrjob.job import MRJob

WORD_RE = re.compile(r"[a-z]+")


class MRWordFrequencyCount(MRJob):
    def mapper(self, _, line):
        for word in WORD_RE.findall(line):
            yield word.lower(), 1

    def reducer(self, key, values):
        yield key, sum(values)


if __name__ == "__main__":
    MRWordFrequencyCount.run()
