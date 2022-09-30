#!/usr/bin/env python3

# Auxiliary script to build figures and plots for the report
# This should only rely on the resources available in the repository
# so that figures can be reproduced with nix

import argparse
import os

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--format", type=str, default="png", choices=["png", "pdf"])
    arg_parser.add_argument(
        "--output", type=str, default="figures", help="Output folder for plots"
    )

    args = arg_parser.parse_args()

    print("Hello World")

    os.makedirs(args.output, exist_ok=True)
