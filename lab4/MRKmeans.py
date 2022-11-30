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
import os
import pathlib
import shutil
import time

import numpy as np
from mrjob.util import to_lines
from MRKmeansStep import MRKmeansStep

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
        "--ncores", default=2, type=int, help="Number of parallel processes to use"
    )

    args = parser.parse_args()
    assign = {}

    # Copies the initial prototypes
    outdir = pathlib.Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)

    shutil.copy(outdir.joinpath(args.prot), outdir.joinpath("prototypes0.txt"))

    nomove = True  # Stores if there has been changes in the current iteration
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
            new_assign = {}
            new_proto = {}
            # Process the results of the script iterating the (key,value) pairs
            for key, value in mr_job1.parse_output(runner1.cat_output()):
                # You should store things here probably in a datastructure
                new_assign[key] = value[0]
                new_proto[key] = value[1]

            nomove = new_assign == assign

            # Saves the new prototypes
            with open(outdir.joinpath("prototypes%d.txt" % (i + 1)), "w") as f:
                for key in new_proto:
                    f.write(
                        str(key)
                        + ":"
                        + " ".join(map(lambda x: f"{x[0]}+{x[1]}", new_proto[key]))
                        + "\n"
                    )

            # If your scripts returns the new assignments you could write them in a file here
            # with open(cwd + '/assignments%d.txt' % (i + 1), 'w') as f:
            #     for key, value in new_assign.items():
            #         f.write(key + ':' + " ".join(value) + '\n')

            # You should store the new prototypes here for the next iteration

            # If you have saved the assignments, you can check if they have changed from the previous iteration

        print(f"Time= {(time.time() - tinit)} seconds")

        if nomove:  # If there is no changes in two consecutive iteration we can stop
            print("Algorithm converged")
            break

    # Now the last prototype file should have the results
