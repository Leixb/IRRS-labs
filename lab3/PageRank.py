#!/usr/bin/env python3

from __future__ import annotations

import sys
import time
from heapq import nlargest
from typing import Dict, List, Tuple

import numpy as np
import polars as pl


class Edge:

    list: List[Edge] = []  # list of Edge
    hash: Dict[Tuple[int, int], Edge] = dict()  # hash of edge to ease the match

    def register(self, destination: int):
        # Adds edge to the list and hash using origin->destination as key
        self.pageIndex = len(Edge.list)
        Edge.list.append(self)
        Edge.hash[(self.origin, destination)] = self

    def __init__(self, origin: int, weight: float = 1.0):
        self.origin = origin
        self.weight = weight

    def __repr__(self):
        return "edge: {0} {1}".format(self.origin, self.weight)


class Airport:

    list: List[Airport] = []  # list of Airport
    hash: Dict[str, Airport] = dict()  # hash key IATA code -> Airport

    def register(self):
        # Adds airport to list and hash
        self.pageIndex = len(Airport.list)
        Airport.list.append(self)
        Airport.hash[self.code] = self

    def __init__(self, iden=None, name=None):
        self.code = iden
        self.name = name
        self.routes = []  # input edges
        self.routeHash = dict()
        self.outweight = 0

    def __repr__(self):
        return f"{self.code}\t{self.pageIndex}\t{self.name}"

    def addRoute(self, edge: Edge):
        # Adds incoming route (assumes it doesn't exist)
        self.routes.append(edge)
        self.routeHash[edge] = edge

    def addOutweight(self, weight: float):
        # Adds weight to outgoing routes
        self.outweight += weight

    def addRouteInc(self, edge: Edge):
        # Adds route if it doesn't exist, otherwise increments weight
        # Since we use polars to group repeated routes, this is not
        # used
        if edge in self.routeHash:
            self.routeHash[edge].weight += edge.weight
        else:
            self.addRoute(edge)


def readAirports(fd):
    print("Reading Airport file from {0}".format(fd))
    for code, name in (
        pl.scan_csv(
            fd, has_header=False, null_values=["\\N", ""], infer_schema_length=200
        )
        .select(
            [
                pl.col("column_5").alias("code"),
                pl.concat_str(["column_2", "column_4"], sep=", ").alias("name"),
            ]
        )
        .filter(pl.col("code").str.lengths() == 3)  # filter out non-IATA codes
        .collect()
        .rows()
    ):
        Airport(iden=code, name=name).register()

    print(f"There were {len(Airport.list)} Airports with IATA code")


def readRoutes(fd):
    print(f"Reading Routes file from {fd}")

    unknown_orig = 0
    unknown_dest = 0

    # We use polars to read the file and aggregate the routes
    for destination, df in (
        pl.scan_csv(
            fd,
            has_header=False,
            null_values=["\\N", ""],
        )
        .select(
            [
                pl.col("column_3").alias("origin"),
                pl.col("column_5").alias("destination"),
            ]
        )
        .groupby(["origin", "destination"])
        .agg(pl.count())
        .collect()
        .partition_by("destination", as_dict=True)
    ).items():
        airport_dest = Airport.hash.get(destination)
        if not airport_dest:
            unknown_dest += 1
            continue

        for origin, _, count in df.rows():
            origin_obj = Airport.hash.get(origin)
            if not origin_obj:
                unknown_orig += 1
                continue

            origin_id = origin_obj.pageIndex

            edge = Edge(origin=origin_id, weight=count)
            edge.register(destination=airport_dest.pageIndex)

            origin_obj.addOutweight(count)

            airport_dest.addRoute(edge)

    print(f"There were {unknown_orig} routes with unknown origin")
    print(f"There were {unknown_dest} routes with unknown destination")
    print(f"There were {len(Edge.list)} added routes")


def computePageRanks(l=0.9, maxIterations=1000, atol=1e-10):
    # compute the PageRanks of the airports
    #
    # l: the damping factor
    # maxIterations: the maximum number of iterations
    # atol: the tolerance for the stopping criterion

    # number of airports (vertices in G)
    n = len(Airport.list)

    p = np.ones(n) / n  # initial probability vector
    for iterations in range(maxIterations):
        q = np.zeros(n)  # new probability vector
        for i, airport in enumerate(Airport.list):
            for edge in airport.routes:
                q[i] += (
                    p[edge.origin] * edge.weight / Airport.list[edge.origin].outweight
                )
            # Apply the damping factor
            q[i] = l * q[i] + (1 - l) / n

        # Normalize q
        q /= np.sum(q)

        # Check convergence
        if np.allclose(p, q, atol=atol):
            break

        p = q

    return p, iterations


def outputPageRanks(p: np.ndarray, top_n=10):
    pr_airports = zip(Airport.list, p)

    print(f"Top {top_n} airports by PageRank:")
    for airport, pr in nlargest(top_n, pr_airports, key=lambda x: x[1]):
        print(f"{pr:.6f}\t{airport}")


def main(argv=None):
    readAirports("airports.txt")
    readRoutes("routes.txt")
    time1 = time.time()
    p, iterations = computePageRanks()
    time2 = time.time()
    outputPageRanks(p)
    print("#Iterations:", iterations)
    print("Time of computePageRanks():", time2 - time1)


if __name__ == "__main__":
    sys.exit(main())
