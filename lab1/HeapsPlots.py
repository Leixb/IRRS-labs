#!/usr/bin/env python


import argparse
import csv
import pathlib
from itertools import takewhile
from typing import Callable, Generator, Iterable, Tuple

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import numpy.lib.recfunctions as rfn
import numpy.typing as npt
import pandas as pd
import seaborn as sns
from common import R2, RMSE, fit_curve, set_theme
from cycler import cycler
from matplotlib.backends.backend_pdf import PdfPages
from scipy.optimize import curve_fit


def f(words: int, k: float, beta: float) -> float:
    return k * np.power(words, beta)


def fit_and_plot_novel(
    filename: str,
    title: str,
    author: str,
    group: pd.DataFrame,
    gutenberg_legal_lenght: int = 3150,
) -> (plt.Figure, Iterable):
    print("Processing novel", filename, title, "by", author)

    # Sort data by number of words so plots are not a mess
    group.sort_values(by="words", inplace=True)

    # Remove the last data with Gutenberg legal terms:
    N = group["words"].iloc[-1]
    words_fit = np.fromiter(
        takewhile(lambda x: x < N - gutenberg_legal_lenght, group["words"]),
        dtype=int,
    )
    unique_fit = group["unique"][: len(words_fit)]

    # Fit the curve ignoring the last point (affected by Gutenberg legalese)
    popt, _, f_fit = fit_curve(
        f,
        words_fit,
        unique_fit,
        p0=(10.0, 0.5),  # Reasonable initial guesses
        bounds=([0.0, 0.0], [np.inf, 1.0]),  # k > 0, 0 < beta < 1
    )

    # Calculate R2 and RMSE
    y_fit = f_fit(words_fit)
    r2 = R2(unique_fit, y_fit)
    rmse = RMSE(unique_fit, y_fit)

    # Save fit data for later
    fit_info = [filename, title, author, *popt, N, r2, rmse]

    # Plot the data
    fig, ax = plt.subplots()
    plt.scatter(words_fit, unique_fit, marker=".", label="Data")
    plt.title(author)
    plt.scatter(
        group["words"][len(words_fit) :],
        group["unique"][len(words_fit) :],
        marker=".",
        label="Gutenberg legalese",
        color="g",
    )
    # ax = group.plot(
    #     x="words", y="unique", title=author, kind="scatter", label="Data", marker="."
    # )
    # We use a plot title as a subtitle and figure title as the actual title
    # x parameter is to make sure the title is centered on the plot and not
    # the whole figure
    left_adj, right_adj = 0.12, 0.90
    plt.suptitle(title, x=(left_adj + right_adj) / 2, horizontalalignment="center")
    plt.subplots_adjust(left=left_adj, right=right_adj)

    plt.xlim(left=0)
    plt.ylim(bottom=0)

    plt.xlabel("Words ($N$)")
    plt.ylabel("Unique words ($V_R$)")

    # Do not scale limits to the fit data (we want it to go from limit to limit)
    plt.autoscale(False)

    points = np.linspace(0, group["words"][-1] * 1.1, 150)
    plt.plot(points, f_fit(points), color="r", label="Herdan-Heaps law fit")

    # plt.legend(["Data", "Herdan-Heaps law fit"], loc="lower right")
    plt.legend(loc="lower right")

    # Text box with fit parameters and R2
    ax.text(
        0.96,
        0.3,
        "\n".join(
            (
                r"$V_R(N) = kN^\beta$",
                r"$\quad\beta=%.2f$" % (popt[1],),
                r"$\quad k=%.2f$" % (popt[0],),
                r"\null",
                r"$R^2=%.4f$" % (r2,),
            )
        ),
        transform=ax.transAxes,
        fontsize=14,
        horizontalalignment="right",
        verticalalignment="bottom",
        bbox=dict(
            boxstyle="round,pad=0.5,rounding_size=0.2",
            facecolor="white",
            alpha=0.8,
            edgecolor="r",
        ),
    )

    # Annotation showing the source txt file
    plt.figtext(
        0.01,
        0.01,
        f" source: \\texttt{{{filename}.txt}}",
        ha="left",
        fontsize=8,
        color="gray",
    )

    # Use scientific notation since the numbers are large
    ax.ticklabel_format(axis="both", style="sci", scilimits=(3, 3))

    return ax.get_figure(), fit_info


def plot_fit_data(fit_data: pd.DataFrame):
    # Plot of fit data
    fig, ax = plt.subplots()

    # Since we have lots of different novels, we need to change both the
    # color and the linestyle to distinguish them properly
    style_cycler = cycler(color=sns.color_palette()) * cycler(
        linestyle=["-", "--", "-.", ":"]
    )
    ax.set_prop_cycle(style_cycler)

    # Sort by descending number of words so that the lines are not as obscured
    fit_data.sort_values(by="N", inplace=True, ascending=False)

    # Add fit line for each novel into a single plot
    for row in fit_data.itertuples():
        x = np.linspace(0, row.N, 100)
        y = f(x, row.k, row.beta)

        # Truncate the titles so they fit in legend
        truncated_title = row.title[:20] + "..." if len(row.title) > 20 else row.title

        # Special case for The Works of Edgar Allan Poe to show the volume number
        if row.file.startswith("PoeWorksVol"):
            truncated_title = f"The Works of Edg... ({row.file[-1]})"

        plt.plot(x, y, label=truncated_title)

    plt.title("Herdan-Heaps law fits")
    plt.xlabel("Words ($N$)")
    plt.ylabel("Unique words ($V_R$)")
    plt.xlim(left=0)
    plt.ylim(bottom=0)

    # Massive legend to the side
    plt.legend(
        fontsize=6,
        title_fontsize=8,
        title=r"Novel $\left(\downarrow N\right)$",
        bbox_to_anchor=(1.01, 0.5),
        loc="center left",
        borderaxespad=0,
    )
    # Make space for the legend
    plt.subplots_adjust(right=0.75)

    # scientific notation as before
    ax.ticklabel_format(axis="both", style="sci", scilimits=(3, 3))

    return fig


def main(
    input: str = "./results/heaps.csv",
    output_dir="./figures",
    tables_dir="./tables",
    titles_file: str = "./titles.csv",
):

    # Nice looking seaborn plots for latex documents
    save_args = set_theme()

    output_dir = pathlib.Path(output_dir)
    tables_dir = pathlib.Path(tables_dir)

    output_dir.mkdir(exist_ok=True)
    tables_dir.mkdir(exist_ok=True)

    gutenberg_legal_lenght = 3150  # Approx

    # Read the data and set columns and index
    df = pd.read_csv(input, index_col=0)

    # Helper table to map file names to titles and authors
    with open(titles_file, mode="r") as titles:
        reader = csv.DictReader(titles, delimiter=";")
        file_to_title_author = {
            row["Filename"]: (row["Title"], row["Author"]) for row in reader
        }
    # Dataframe to collect the fit restults
    fit_data = pd.DataFrame(
        columns=["file", "title", "author", "k", "beta", "N", "R2", "RMSE"]
    )

    # All the plots into a single PDF, one page per plot
    with PdfPages(output_dir.joinpath("heaps.pdf")) as pdf:
        # Plot Herdan-Heaps law for each novel
        for filename, group in df.groupby("novel"):
            title, author = file_to_title_author[filename]
            fig, fit_info = fit_and_plot_novel(
                filename, title, author, group, gutenberg_legal_lenght
            )
            pdf.savefig(fig, **save_args)
            plt.close(fig)
            fit_data.loc[len(fit_data)] = fit_info

    # Save fit data to a LaTeX table
    fit_data.style.to_latex(tables_dir.joinpath("heaps.tex"))

    fig = plot_fit_data(fit_data)
    fig.savefig(output_dir.joinpath("heaps_all.pdf"), **save_args)


if __name__ == "__main__":
    main()
