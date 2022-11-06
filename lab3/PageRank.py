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


class Route:
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
        r = Route()
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
                r.departureNum = temp[1]
                r.departure = temp[2]
                r.arrivalNum = temp[3]
                r.arrival = temp[4]
                r.count = 1
                r.id = temp[2] + temp[4]
                edgeList.append(r)
                edgeHash[r.id] = r
    routesTxt.close()
    print(f"There were {cont} Routes with IATA codes")


def computePageRanks():
    size = len(airportList)
    l = 0.9
    p = np.zeros((size, size))
    i = 0
    j = 0
    for i in range(size):
        a1 = airportList[i]
        for j in range(size):
            a2 = airportList[j]
            edge = edgeHash.get(a1.code + a2.code)
            if edge:
                p[i][j] = edge.count  # fill the matrix with the out degrees
        p[i] = normalize(
            p[i]
        )  # Normalising the matrix sometimes gives a total of 0.9999...
        if np.sum(p[i]) > 0.2:  # applying the google algorithm
            p[i] = p[i] * l + (1 - l) / size
        else:  # case of all zero vectors
            p[i] = p[i] * 0 + 1 / size

    pi = np.ones(size, float) / size  # uniform PI(0)

    # p = np.array([[0.8,0.15,0.05],
    #                 [0.7,0.2,0.1],
    #                 [0.5,0.3,0.2]])
    # pi = np.array([0.2,0.2,0.6])

    # Stationary distribution
    n = 0
    while n < 1000:
        n += 1
        res = np.dot(pi, p)
        diff = pi - res
        if max(np.abs(diff)) < 10e-10:
            break
        pi = res
    print(pi, np.sum(pi))
    return n


def outputPageRanks():
    pass
    # write your code


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
