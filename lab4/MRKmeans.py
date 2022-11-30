#!/usr/bin/env python3
"""
.. module:: MRKmeans

MRKmeans
*************

:Description: MRKmeans

    Iterates the MRKmeansStep script

:Authors: bejar


:Version:

:Created on: 17/07/2017 10:16

"""

import argparse
import pathlib
import shutil
import time
from multiprocessing import cpu_count
from typing import Dict, List

from MRKmeansStep import Assignment, Key, MRKmeansStep, Prototype

__author__ = "bejar"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prot", default="prototypes.txt", help="Initial prototpes file"
    )
    parser.add_argument("--output", default=".", help="Output directory")
    parser.add_argument("--docs", default="documents.txt", help="Documents data")
    parser.add_argument("--iter", default=5, type=int, help="Number of iterations")
    parser.add_argument(
        "-n",
        "--ncores",
        "--nproc",
        default=min(1, cpu_count() - 2),
        type=int,
        help="Number of parallel processes to use",
    )

    args = parser.parse_args()
    assign: Dict[Key, Assignment] = {}

    assign_values: List[Assignment] = []

    # Copies the initial prototypes
    outdir = pathlib.Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)

    shutil.copy(args.prot, outdir.joinpath("prototypes0.txt"))

    moved = False  # Stores if there has been changes in the current iteration
    for i in range(args.iter):
        tinit = time.time()  # For timing the iterations

        # Configures the script
        print("Iteration %d ..." % (i + 1))
        # The --file flag tells to MRjob to copy the file to HADOOP
        # The --prot flag tells to MRKmeansStep where to load the prototypes from
        mr_job1 = MRKmeansStep(
            args=[
                "-r",
                "local",
                args.docs,
                "--file",
                str(outdir.joinpath("prototypes%d.txt" % i)),
                "--prot",
                str(outdir.joinpath("prototypes%d.txt" % i)),
                "--num-cores",
                str(args.ncores),
            ]
        )

        # Runs the script
        with mr_job1.make_runner() as runner1:
            runner1.run()

            new_assign: Dict[Key, Assignment] = {}
            new_proto: Dict[Key, Prototype] = {}
            # Process the results of the script iterating the (key,value) pairs
            for key, value in mr_job1.parse_output(runner1.cat_output()):
                new_assign[key], new_proto[key] = value

        # Check if there has been changes in the assignment
        #
        # We cannot use the following, because the names of the
        # clusters may have swapped:
        # moved = new_assign != assign
        #
        # Instead, we check the ordered assignments of the
        # clusters:
        new_assign_values = sorted(new_assign.values())
        moved = assign_values != new_assign_values

        assign = new_assign
        assign_values = new_assign_values

        # Saves the new prototypes
        with open(outdir.joinpath("prototypes%d.txt" % (i + 1)), "w") as f:
            for key in new_proto:
                f.write(
                    key
                    + ":"
                    + " ".join(map(lambda x: f"{x[0]}+{x[1]}", new_proto[key]))
                    + "\n"
                )

        # Saves the new assignments
        with open(outdir.joinpath("assignments%d.txt" % (i + 1)), "w") as f:
            for key, value in new_assign.items():
                f.write(key + ":" + " ".join(value) + "\n")

        # If there is no changes in two consecutive iteration we can stop
        if not moved:
            print("Algorithm converged")
            break

        print(f"Time= {(time.time() - tinit)} seconds")
