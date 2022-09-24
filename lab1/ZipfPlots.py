#!/usr/bin/env python3

import argparse
import pathlib
from typing import Callable, Generator, Iterable, Tuple

import matplotlib.pyplot as plt
import numpy as np
import numpy.lib.recfunctions as rfn
import numpy.typing as npt
import seaborn as sns
from scipy.optimize import curve_fit


def parse_file(file: Iterable[str]) -> Generator[Tuple[int, str], None, None]:

    for line in file:
        split = line.strip().split(", ")

        if len(split) == 2:
            yield int(split[0]), split[1]


def filter_sort_and_rank(data: Iterable[Tuple[int, str]]) -> npt.NDArray:
    data = np.fromiter(
        filter(lambda x: x[1].isalpha(), data),
        dtype=[("count", int), ("word", str)],
    )

    data[::-1].sort()  # Sort in descending order (inplace)

    return rfn.append_fields(data, "rank", np.arange(1, len(data) + 1))


def fit_curve(
    f: Callable[..., float], x: npt.NDArray, y: npt.NDArray, **kwargs
) -> Tuple[float, float, Callable[[npt.NDArray], float]]:
    popt, pcov = curve_fit(
        f,
        x,
        y,
        **kwargs,
    )
    f_fit = np.vectorize(lambda rank: f(rank, *popt))

    return popt, pcov, f_fit


def generate_plots(
    data: npt.NDArray,
    f_fit: Callable[[npt.NDArray], float],
    format: str = "png",
    folder: str = "figures",
) -> None:
    # Set LaTeX font theme for plots using seaborn
    sns.set_theme(
        context="paper",
        style="whitegrid",
        font_scale=1.5,
        font="STIXGeneral",
        rc={
            "text.usetex": True,
        },
    )

    save_args = {"bbox_inches": "tight", "dpi": 300}

    # Make sure the output folder exists
    destination = pathlib.Path(folder)
    destination.mkdir(parents=True, exist_ok=True)

    ax = plt.subplot(1, 1, 1)

    plt.plot(data["rank"], data["count"])
    plt.plot(data["rank"], f_fit(data["rank"]))

    plt.legend(["Data", "Fit"])
    plt.xlabel("Rank")
    plt.ylabel("Frequency")

    plt.savefig(destination.joinpath(f"zipf.{format}"), **save_args)

    # Same plot but on a log-log scale
    plt.yscale("log")
    plt.xscale("log")

    # Add minor ticks to emphasize the log-log scale
    ax.grid(visible=True, which="minor", color="whitesmoke")
    ax.minorticks_on()

    plt.savefig(destination.joinpath(f"zipf_loglog.{format}"), **save_args)


def main(input, output: str, format: str = "png", skip: int = 0) -> None:
    if type(input) is str:
        input = pathlib.Path(input).read_text().splitlines()
    data = filter_sort_and_rank(parse_file(input))

    print(data[:10])

    def f(rank: int, a: float, b: float, c: float) -> float:
        return c * np.power((rank + b), -a)

    popt, _, f_fit = fit_curve(
        f,
        data["rank"],
        data["count"],
        p0=(1.0, 1.0, 1.0),
        bounds=([0.0, 0.0, 0.0], [np.inf, np.inf, np.inf]),
    )
    print(popt)

    generate_plots(data, f_fit, format, output)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-i", "--input", type=argparse.FileType("r"), default="data.txt"
    )
    arg_parser.add_argument("--format", type=str, default="png", choices=["png", "pdf"])
    arg_parser.add_argument(
        "--skip", type=int, default=0, help="Skip first n words when computing fit"
    )
    arg_parser.add_argument(
        "--output", type=str, default="figures", help="Output folder for plots"
    )

    args = arg_parser.parse_args()
    main(args.input, args.output, args.format, args.skip)
