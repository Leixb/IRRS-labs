#!/usr/bin/env python3

import argparse

import HeapsPlots
import ZipfPlots

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-Z", "--zipf-input", type=argparse.FileType("r"), default="./results/zipf.csv"
    )
    arg_parser.add_argument(
        "-H",
        "--heaps-input",
        type=argparse.FileType("r"),
        default="./results/heaps.csv",
    )
    arg_parser.add_argument("--format", type=str, default="png", choices=["png", "pdf"])
    arg_parser.add_argument(
        "--skip", type=int, default=0, help="Skip first n words when computing fit"
    )
    arg_parser.add_argument(
        "--output", type=str, default="figures", help="Output folder for plots"
    )

    args = arg_parser.parse_args()

    ZipfPlots.main(args.zipf_input, args.output, format="pdf", skip=args.skip)
    HeapsPlots.main(args.heaps_input, args.output)
