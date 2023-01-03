#!/usr/bin/env python

import csv
import os
import pathlib
from itertools import chain

import networkx as nx
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics import pairwise_distances_chunked
from sklearn.metrics.pairwise import linear_kernel

folder = (os.environ.get("DATA") or "./data") + "/arxiv_abs"

files = list(filter(lambda x: x.is_file(), pathlib.Path(folder).glob("**/*")))
print(files[:5])

# save file names
with open("files.csv", "w") as f:
    writer = csv.writer(f)
    for i, file in enumerate(files):
        writer.writerow([i, file.parent.name, file.name])

# vectorizer = CountVectorizer(input='filename') # faster alternative to tfidf
vectorizer = TfidfVectorizer(input="filename")
X = vectorizer.fit_transform(files)

print(X.shape)

# build similarity matrix

# similarity = linear_kernel(X, dense_output=False) # same as cosine_similarity (when TfidfVectorizer is used) but faster
# similarity = cosine_similarity(X)
# print(similarity.shape)

# we cannot do this in memory, instead we process it by chunks and reduce it
# to an adjacency list using a threshold

# Adjust threshold so that it is connex
threshold = 0.7


def reduce_func(D_chunk, start):
    neigh = [np.flatnonzero(d < threshold) for d in D_chunk]
    return neigh


gen = pairwise_distances_chunked(
    X, metric="cosine", working_memory=None, reduce_func=reduce_func
)

adj_list = []

with open("output.csv", "w") as f:
    writer = csv.writer(f)
    for i, chunk in enumerate(gen):
        print(i)

        for row in chunk:
            row_l = row.tolist()
            adj_list.append(row_l)
            writer.writerow(row_l)


G = nx.Graph()

for i, row in enumerate(adj_list):
    # add only if i < j
    G.add_edges_from([(i, j) for j in row if i < j])

print(nx.info(G))

nx.write_gexf(G, "graph.gexf")

# TODO: fix this
#
# - add node attributes (at least the file name)
# - for some reason there are too many nodes
# - remove unconnected nodes
# - remove self loops
# - skip duplicated edges
