#!/usr/bin/env python


import csv
from itertools import takewhile
from typing import Callable, Generator, Iterable, Tuple

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import numpy.lib.recfunctions as rfn
import numpy.typing as npt
import pandas as pd
import seaborn as sns
from cycler import cycler
from matplotlib.backends.backend_pdf import PdfPages
from scipy.optimize import curve_fit

# Nice looking seaborn plots for latex documents
sns.set_theme(
    context="paper",
    style="whitegrid",
    font_scale=1.5,
    font="STIXGeneral",
    rc={
        "text.usetex": True,
    },
)

save_args = {"dpi": 300}

guttenberg_legal_lenght = 3086


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


# Read the data and set columns and index
df = pd.read_csv("./data/uniq_data.txt", sep="\t", header=None)

df.columns = ["novel", "split", "unique", "words"]

df.set_index(["novel", "split"], inplace=True)
df.sort_index(inplace=True)


def f(words: int, k: float, beta: float) -> float:
    return k * np.power(words, beta)


# Helper table to map file names to titles and authors
file_to_title_author = dict()
with open("./data/novels/titles.csv", mode="r") as titles:
    reader = csv.reader(titles, delimiter=";")
    next(reader)
    for row in reader:
        file_to_title_author[row[0]] = (row[1], row[2])


def R2(y: npt.NDArray, y_fit: npt.NDArray) -> float:
    y_mean = np.mean(y)
    ss_tot = np.sum(np.power(y - y_mean, 2))
    ss_res = np.sum(np.power(y - y_fit, 2))

    return 1 - ss_res / ss_tot


def RMSE(y: npt.NDArray, y_fit: npt.NDArray) -> float:
    return np.sqrt(np.mean(np.power(y - y_fit, 2)))


# Dataframe to collect the fit restults
fit_data = pd.DataFrame(
    columns=["file", "title", "author", "k", "beta", "N", "R2", "RMSE"]
)

# All the plots into a single PDF, one page per plot
with PdfPages("figures/heaps.pdf") as pdf:
    # Plot Herdan-Heaps law for each novel
    for key, group in df.groupby("novel"):

        # Get nice title and author
        title, author = file_to_title_author[key]

        print("Processing novel", key, title, "by", author)

        # Sort data by number of words so plots are not a mess
        group.sort_values(by="words", inplace=True)

        # Remove the last data with Guttenberg legal terms:
        N = group["words"].iloc[-1]
        words_fit = np.fromiter(
            takewhile(lambda x: x < N - guttenberg_legal_lenght, group["words"]),
            dtype=int,
        )
        unique_fit = group["unique"][: len(words_fit)]

        # Fit the curve ignoring the last point (affected by Guttenberg legalese)
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
        fit_data.loc[len(fit_data)] = [key, title, author, *popt, N, r2, rmse]

        # Plot the data (zorder 2 so it is on top of the fit)
        ax = group.plot(
            x="words", y="unique", title=author, kind="scatter", zorder=2, label="Data"
        )
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

        # All the documents contain Project Guttenberg legalese at the end
        # Display it as a vertical line
        plt.vlines(
            N - guttenberg_legal_lenght,
            ymin=0,
            ymax=N * 1.1,
            linestyles="dashed",
            zorder=1,
            label="Gutenberg legalese",
            colors=["g"],
        )

        points = np.linspace(0, group["words"][-1] * 1.1, 150)
        plt.plot(
            points, f_fit(points), color="r", zorder=1, label="Herdan-Heaps law fit"
        )

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
            f" source: \\texttt{{{key}.txt}}",
            ha="left",
            fontsize=8,
            color="gray",
        )

        # Use scientific notation since the numbers are large
        ax.ticklabel_format(axis="both", style="sci", scilimits=(3, 3))

        fig = ax.get_figure()
        pdf.savefig(fig, **save_args)
        plt.close(fig)


# Save fit data to a CSV file
fit_data.to_csv("data/heaps_fit_data.csv", index=False)

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

plt.savefig("figures/heaps_all.pdf", **save_args)
