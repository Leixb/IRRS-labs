#!/usr/bin/env python3

import argparse
import time
from collections import defaultdict

import numpy as np
import polars as pl
from PageRank import computePageRanks, readAirports, readRoutes

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Benchmarking script")
    parser.add_argument(
        "--airports",
        default="airports.txt",
        help="The file containing the airports data",
    )
    parser.add_argument(
        "--routes",
        default="routes.txt",
    )
    parser.add_argument(
        "-r",
        "--repetitions",
        help="Number of repetitions per parameter",
        type=int,
        default=5,
    )
    parser.add_argument(
        "-l",
        "--damping",
        help="Values to test for the damping parameter",
        type=float,
        nargs="+",
        default=[0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.99],
    )
    parser.add_argument(
        "-t",
        "--tolerance",
        help="Tolerance for the convergence criterion",
        type=float,
        nargs="+",
        default=[1e-6, 1e-7, 1e-8, 1e-9, 1e-10],
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=1000,
        help="The maximum number of iterations",
    )
    args = parser.parse_args()

    readAirports(args.airports)
    readRoutes(args.routes)

    results = defaultdict(list)

    for damping in args.damping:
        for atol in args.tolerance:
            for _ in range(args.repetitions):
                time1 = time.time()
                p, iterations = computePageRanks(damping, args.max_iterations, atol)
                time2 = time.time()

                p_q = np.quantile(p, [0, 0.25, 0.5, 0.75, 1])

                results["damping"].append(damping)
                results["tolerance"].append(atol)
                results["iterations"].append(iterations)
                results["time"].append(time2 - time1)
                results["p_min"].append(p_q[0])
                results["p_25"].append(p_q[1])
                results["p_50"].append(p_q[2])
                results["p_75"].append(p_q[3])
                results["p_max"].append(p_q[4])
            print("damping: {}, tolerance: {}".format(damping, atol))

    df = pl.DataFrame(results)
    df.write_csv("results_all.csv")
    df.groupby(["damping", "tolerance"]).mean().write_csv("results.csv")
