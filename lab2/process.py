#!/usr/bin/env python3

# Auxiliary script to build figures and plots for the report
# This should only rely on the resources available in the repository
# so that figures can be reproduced with nix

import argparse

import plotsFirstPart

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--format", type=str, default="pdf", choices=["png", "pdf"])
    arg_parser.add_argument(
        "--output", type=str, default="figures", help="Output folder for plots"
    )

    args = arg_parser.parse_args()

    plotsFirstPart.main(output_dir=args.output, format=args.format)
