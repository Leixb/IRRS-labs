#!/usr/bin/env python

import os
import pathlib

from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

# count vectorizer from files in folder

folder = (os.environ.get("DATA") or "./data") + "/arxiv_abs"

# all files in folder and subfolders
files = filter(lambda x: x.is_file(), pathlib.Path(folder).glob("**/*"))

# vectorizer = CountVectorizer(input='filename')
vectorizer = TfidfVectorizer(input="filename")
X = vectorizer.fit_transform(files)

print(X.shape)

# build similarity matrix

import csv

# from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics.pairwise import linear_kernel

# this takes too much memory
# similarity = cosine_similarity(X)
# similarity = linear_kernel(X, dense_output=False)
# print(similarity.shape)


with open("results.csv", "a") as f:
    writer = csv.writer(f)

    # process by chunks
    chunk_size = 1000
    for i in range(0, X.shape[0], chunk_size):
        print(i)
        similarity = linear_kernel(X[i : min(i + chunk_size, X.shape[0])], X)
        for j in range(similarity.shape[0]):
            writer.writerow(similarity[j])

# save similarity matrix

# import numpy as np

# np.save('similarity.npy', similarity)

# # convert to boolean with a threshold

# import numpy as np

# threshold = 0.5

# similarity_bool = np.where(similarity > threshold, 1, 0)

# print(similarity_bool.shape)

# # now build the network

# import networkx as nx

# G = nx.from_numpy_matrix(similarity_bool)

# print(nx.info(G))


# # save pickle

# nx.write_gpickle(G, "arxiv_abs.gpickle")
