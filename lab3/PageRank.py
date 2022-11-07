#!/usr/bin/env python3

import sys
import time
from collections import namedtuple

import numpy as np


class Edge:
    def __init__(self, origin=None):
        self.origin = ...  # write appropriate value
        self.weight = ...  # write appropriate value

    def __repr__(self):
        return "edge: {0} {1}".format(self.origin, self.weight)

    ## write rest of code that you need for this class


class Airport:
    def __init__(self, iden=None, name=None):
        self.code = iden
        self.name = name
        self.routes = []
        self.routeHash = dict()
        self.outweight = ...  # write appropriate value

    def __repr__(self):
        return f"{self.code}\t{self.pageIndex}\t{self.name}"


class Edge:
    def __init__(
        self, departure=None, arrival=None, depNum=None, arrivNum=None, ident=None
    ):
        self.departure = departure
        self.departureNum = depNum
        self.arrival = arrival
        self.arrivalNum = arrivNum
        self.id = ident
        self.count = 0


edgeList = []  # list of Edge
edgeHash = dict()  # hash of edge to ease the match
airportList = []  # list of Airport
airportHash = dict()  # hash key IATA code -> Airport
steadyState = []  # the steady stade probability vector


def readAirports(fd):
    print(f"Reading Airport file from {fd}")
    airportsTxt = open(fd, "r", encoding="utf-8")
    cont = 0
    for line in airportsTxt.readlines():
        a = Airport()
        try:
            temp = line.split(",")
            if len(temp[4]) != 5:
                raise Exception("not an IATA code")
            a.name = temp[1][1:-1] + ", " + temp[3][1:-1]
            a.code = temp[4][1:-1]
        except Exception as inst:
            pass
        else:
            cont += 1
            airportList.append(a)
            airportHash[a.code] = a
    airportsTxt.close()
    print(f"There were {cont} Airports with IATA code")


def readRoutes(fd):
    print(f"Reading Routes file from {fd}")
    routesTxt = open(fd, "r")
    cont = 0
    for line in routesTxt.readlines():
        r = Edge()
        try:
            temp = line.split(",")
            if len(temp[2]) != 3 or len(temp[4]) != 3:
                raise Exception("not an IATA code")
        except Exception as inst:
            pass
        else:
            edge = edgeHash.get(temp[2] + temp[4])
            if edge:
                edge.count += 1
            else:
                cont += 1
                # r.departureNum = temp[1]
                # r.departure = temp[2]
                # r.arrivalNum = temp[3]
                # r.arrival = temp[4]
                r.count = 1
                r.id = temp[2] + temp[4]
                edgeList.append(r)
                edgeHash[r.id] = r
    routesTxt.close()
    print(f"There were {cont} Routes with IATA codes")


def computePageRanks(l=0.9, maxIterations=1000, epsilon=1e-10):
    # compute the PageRanks of the airports
    #
    # l: the damping factor
    # maxIterations: the maximum number of iterations
    # epsilon: the convergence criterion

    global steadyState
    n = len(airportList)
    p = np.zeros((n, n))

    for i, a1 in enumerate(airportList):
        for j, a2 in enumerate(airportList):
            edge = edgeHash.get(a1.code + a2.code)
            if edge:
                p[i][j] = edge.count  # fill the matrix with the out degrees

        # Normalising the matrix sometimes gives a total of 0.9999...
        p[i] = normalize(p[i])

        if np.sum(p[i]) > 0.2:  # applying the google algorithm
            p[i] = p[i] * l + (1 - l) / n
        else:  # case of all zero vectors
            p[i] = np.ones(n, float) / n

    # Create vector with 1/n in each position
    pi = np.ones(n, float) / n  # uniform PI(0)

    # p = np.array([[0.8,0.15,0.05],
    #                 [0.7,0.2,0.1],
    #                 [0.5,0.3,0.2]])
    # pi = np.array([0.2,0.2,0.6])

    # Stationary distribution
    for n in range(maxIterations):
        res = np.dot(pi, p)
        diff = pi - res
        if max(np.abs(diff)) < epsilon:
            break
        pi = res

    print(pi, np.sum(pi))
    steadyState = np.array(pi).copy()
    return n


def outputPageRanks():
    with open("output.txt", "w", encoding="utf-8") as f:
        for ind in np.argsort(-steadyState):
            print(
                f"Airport: {airportList[ind].name}, page rank: {steadyState[ind]}",
                file=f,
            )


def normalize(vect):
    size = np.sum(vect)
    if size != 0:
        vect = vect / size
    return vect


def main(argv=None):
    readAirports("airports.txt")
    readRoutes("routes.txt")
    time1 = time.time()
    iterations = computePageRanks()
    time2 = time.time()
    outputPageRanks()
    print("#Iterations:", iterations)
    print("Time of computePageRanks():", time2 - time1)


if __name__ == "__main__":
    sys.exit(main())
