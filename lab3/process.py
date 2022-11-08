#!/usr/bin/env python3

# Auxiliary script to build figures and plots for the report
# This should only rely on the resources available in the repository
# so that figures can be reproduced with nix

import argparse
import pathlib
import shutil

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--format", type=str, default="pdf", choices=["png", "pdf"])
    arg_parser.add_argument(
        "--output", type=str, default="figures", help="Output folder for plots"
    )

    args = arg_parser.parse_args()

    out = pathlib.Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    # We should generate the outputs properly
    # But since it takes a while, we just copy
    # the pre-generated ones to the appropriate folder

    # copy files into folder
    file_names = ["output.txt", "output_08.txt", "results.csv", "PageRank.py"]

    for file_name in file_names:
        shutil.copy(file_name, out.parent / file_name)
