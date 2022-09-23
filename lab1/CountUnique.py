#!/usr/bin/env python


from typing import Callable, Generator, Iterable, Tuple

import matplotlib.pyplot as plt
import numpy as np
import numpy.lib.recfunctions as rfn
import numpy.typing as npt
import pandas as pd
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from scipy.optimize import curve_fit

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


def fit_curve(
    f: Callable[..., float], x: npt.NDArray, y: npt.NDArray
) -> Tuple[float, float, Callable[[npt.NDArray], float]]:
    popt, pcov = curve_fit(f, x, y)

    f_fit = np.vectorize(lambda rank: f(rank, *popt))

    return popt, pcov, f_fit


# Read the data
df = pd.read_csv("./data/uniq_data.txt", sep="\t", header=None)

df.columns = ["novel", "split", "unique", "words"]

df.sort_index(inplace=True)

df.set_index(["novel", "split"], inplace=True)

print(df.head())


def f(words: int, k: float, beta: float) -> float:
    return k * np.power(words, beta)


# create df2
with PdfPages("heaps.pdf") as pdf:
    for key, group in df.groupby("novel"):

        print("Processing novel", key)

        group.sort_values(by="words", inplace=True)
        popt, _, f_fit = fit_curve(f, group["words"], group["unique"])

        ax = group.plot(x="words", y="unique", title=key, legend=False, kind="scatter")

        plt.plot(group["words"], f_fit(group["words"]), color="r")
        plt.legend(["fit", "data"], loc="lower right")

        textstr = "\n".join(
            (
                r"$\beta=%.2f$" % (popt[1],),
                r"$k=%.2f$" % (popt[0],),
            )
        )

        # these are matplotlib.patch.Patch properties
        props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)

        # place a text box in upper left in axes coords
        ax.text(
            0.05,
            0.95,
            textstr,
            transform=ax.transAxes,
            fontsize=14,
            verticalalignment="top",
            bbox=props,
        )

        fig = ax.get_figure()
        pdf.savefig(fig, **save_args)
        plt.close(fig)
