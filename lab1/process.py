#!/usr/bin/env python3

import argparse
import sys
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-i", "--input", type=argparse.FileType("r"), default=sys.stdin
    )
    arg_parser.add_argument("--format", type=str, default="png")
    args = arg_parser.parse_args()

    data: List[Tuple[str, int]] = []

    for line in args.input:
        split = line.strip().split(", ")

        if len(split) != 2:
            print(split, file=sys.stderr)
            continue

        word = split[1]
        if not word.isalpha():
            continue

        count = int(split[0])

        data.append((word, count))

    data.sort(key=lambda x: x[1], reverse=True)

    print(data[:10])

    n = len(data)

    def f(rank: int, a: float, b: float, c: float) -> float:
        return c * np.power((rank + b), -a)

    xdata = np.arange(1, n + 1)
    ydata = np.array([x[1] for x in data])

    popt, pcov = curve_fit(
        f,
        xdata,
        ydata,
        p0=(0.5, 1.0, 1.0),
        bounds=([0.0, 0.0, 0.0], [np.inf, np.inf, np.inf]),
    )

    print(popt)

    plt.plot(xdata, ydata)
    plt.plot(xdata, [f(x, *popt) for x in xdata])
    plt.legend(["data", "fit"])
    plt.savefig(f"figures/plot_freq.{args.format}")

    plt.clf()

    plt.plot(xdata, ydata)
    plt.plot(xdata, [f(x, *popt) for x in xdata])
    plt.yscale("log")
    plt.xscale("log")
    plt.legend(["data", "fit"])
    plt.savefig(f"figures/plot_log_log.{args.format}")
