#!/usr/bin/env python3

import argparse
import pathlib
from typing import Callable, Generator, Iterable, Tuple

import matplotlib.pyplot as plt
import numpy as np
import numpy.lib.recfunctions as rfn
import numpy.typing as npt
import seaborn as sns
import unidecode
from common import R2, fit_curve, set_theme


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


def generate_plots(
    data: npt.NDArray,
    f_fit: Callable[[npt.NDArray], float],
    popt: Tuple[float, float, float],
    name: str = "zipf",
    format: str = "pdf",
    folder: str = "figures",
) -> None:
    # Set LaTeX font theme for plots using seaborn
    save_args = set_theme()

    # Make sure the output folder exists
    destination = pathlib.Path(folder)
    destination.mkdir(parents=True, exist_ok=True)

    ax = plt.subplot(1, 1, 1)

    y_fit = f_fit(data["rank"])

    plt.plot(data["rank"], data["count"], label="Data")
    plt.plot(data["rank"], y_fit, label=name + " fit")

    r2 = R2(data["count"], y_fit)

    plt.xlabel("Rank ($k$)")
    plt.ylabel("Frequency ($f$)")

    ax.text(
        0.05,
        0.05,
        "\n".join(
            (
                r"$f(k) = c (k + b)^{-a}$",
                r"$\quad a=%.2f$" % (popt[0],),
                r"$\quad b=%.2f$" % (popt[1],),
                r"$\quad c=%d$" % (int(popt[2]),),
                r"\null",
                r"$R^2=%.4f$" % (r2,),
            )
        ),
        transform=ax.transAxes,
        fontsize=14,
        horizontalalignment="left",
        verticalalignment="bottom",
        bbox=dict(
            boxstyle="round,pad=0.5,rounding_size=0.2",
            facecolor="white",
            alpha=0.8,
            edgecolor="r",
        ),
    )

    plt.figtext(
        0.01,
        0.01,
        r" data: \texttt{20 Newsgroups}",
        ha="left",
        fontsize=8,
        color="gray",
    )

    plt.legend(loc="upper right")

    # normalize name for file
    name = name.replace(" ", "_").replace("_+_", "_").lower()
    # remove accents
    name = unidecode.unidecode(name)
    plt.savefig(destination.joinpath(f"{name}.{format}"), **save_args)

    # Same plot but on a log-log scale
    plt.yscale("log")
    plt.xscale("log")

    plt.subplots_adjust(right=0.95, top=0.95)

    # Add minor ticks to emphasize the log-log scale
    # ax.grid(visible=True, which="minor", color="whitesmoke")
    # ax.minorticks_on()

    plt.savefig(destination.joinpath(f"{name}_loglog.{format}"), **save_args)


def main(input, output: str, format: str = "png", skip: int = 10) -> None:
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
    )
    print(popt)

    generate_plots(data, f_fit, popt, "ZipF naïve", format, output)

    popt, _, f_fit = fit_curve(
        f,
        data["rank"],
        data["count"],
        p0=(1.0, 1.0, 1.0),
        bounds=([0.0, 0.0, 0.0], [np.inf, np.inf, np.inf]),
    )

    plt.clf()

    generate_plots(data, f_fit, popt, "ZipF bounded", format, output)

    popt, _, f_fit = fit_curve(
        f,
        data["rank"][skip:],
        data["count"][skip:],
        p0=(1.0, 1.0, 1.0),
        bounds=([0.0, 0.0, 0.0], [np.inf, np.inf, np.inf]),
    )

    plt.clf()

    generate_plots(data, f_fit, popt, f"ZipF bounded + skip {skip}", format, output)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-i", "--input", type=argparse.FileType("r"), default="results/zipf.csv"
    )
    arg_parser.add_argument("--format", type=str, default="pdf", choices=["png", "pdf"])
    arg_parser.add_argument(
        "--skip", type=int, default=10, help="Skip first n words when computing fit"
    )
    arg_parser.add_argument(
        "--output", type=str, default="figures", help="Output folder for plots"
    )

    args = arg_parser.parse_args()
    main(args.input, args.output, args.format, args.skip)
