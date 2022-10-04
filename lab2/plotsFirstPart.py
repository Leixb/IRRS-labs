#!/usr/bin/env python3

import pathlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from cycler import cycler

from common import set_theme


def plot_tokenizers(df: pd.DataFrame) -> plt.Figure:
    ax = df.plot.bar(
        x="token",
        y="words",
        rot=0,
        legend=False,
        ylabel="Words",
        xlabel="Tokenizer",
        figsize=(6.4, 2.8),
    )
    ax.xaxis.grid(False)
    ax.ticklabel_format(axis="y", style="sci", scilimits=(3, 3))

    plt.ylim(0, 100e3)
    plt.subplots_adjust(bottom=0.2, right=0.95)

    for w in ax.patches:
        ax.annotate(
            f"{w.get_height()}",
            (w.get_x() + w.get_width() / 2, w.get_height()),
            ha="center",
            va="top",
            xytext=(0, -5),
            textcoords="offset points",
            color="w",
        )

    plt.figtext(
        0.01,
        0.01,
        r" source: \texttt{novels}",
        ha="left",
        fontsize=8,
        color="gray",
    )

    return ax.get_figure()


def colorize(x):
    # max_len = "lowercase-asciifolding-stop-porter_stem-kstem-snowball"
    max_len = "asciifolding-stop-porter_stem-kstem-snowball"
    all = max_len.split("-")
    x = x.split("-")

    out = r"\texttt{\color{lightgray}"
    cnt = 0
    for i in all:
        if i in x:
            cnt += 1
            out += r" \textcolor{black}{" + i + "}"
        else:
            out += " " + i
    out = out + "}" + r" \textcolor[HTML]{1f77b4}" + f"{cnt}"

    if cnt == 0:
        out = r"\textasteriskcentered" + out
    elif cnt == len(all):
        out = "+" + out

    return out


def plot_filters(df: pd.DataFrame) -> plt.Figure:
    # take only the ones which contain lowercase in filter column
    # replace nan with empty string
    dd = df[["filters", "unique"]].fillna("none")
    dd["lowercase"] = dd["filters"].str.startswith("lowercase").fillna(False)
    dd["filters"] = dd["filters"].str.removeprefix("lowercase-")
    dd["filters"] = dd["filters"].str.replace("lowercase", "none")

    dd["filters"] = dd["filters"].apply(colorize)

    fig, ax = plt.subplots()
    ax.set_prop_cycle(cycler("color", ["r", "g"]))
    sns.barplot(x="unique", y="filters", hue="lowercase", data=dd, alpha=0.8)

    plt.xlabel("Unique Words")
    plt.ylabel("Filters")
    plt.legend(loc="lower left", title="Lowercase", framealpha=1)
    ax.yaxis.grid(False)
    ax.ticklabel_format(axis="x", style="sci", scilimits=(3, 3))

    # plt.ylim(0, 100e3)
    plt.subplots_adjust(left=0.5, top=0.98, right=0.98)
    plt.yticks(fontsize=8)

    plt.figtext(
        0.01,
        0.01,
        r" source: \texttt{20\_newsgroups}",
        ha="left",
        fontsize=8,
        color="gray",
    )

    plt.figtext(
        0.475,
        0.08,
        r"number of filters  $\;\nearrow$",
        ha="right",
        fontsize=8,
        color="b",
    )

    return ax.get_figure()


def main(
    token_data="./results/tokenizers_novels.csv",
    filter_data="./results/filters_newsgroups.csv",
    output_dir="./figures",
    tables_dir="./tables",
    format="pdf",
):
    output_dir = pathlib.Path(output_dir)
    tables_dir = pathlib.Path(tables_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    save_args = set_theme()

    # Tokenizers
    df = pd.read_csv(token_data).sort_values("words")
    fig = plot_tokenizers(df)
    fig.savefig(output_dir.joinpath(f"words_token.{format}"), **save_args)

    df[["token", "words"]].set_index("token").style.format(precision=3).to_latex(
        tables_dir.joinpath("tokenizers_novels.tex"), hrules=True
    )

    # Filters
    df = pd.read_csv(filter_data, sep=";").sort_values("unique")
    fig = plot_filters(df)
    fig.savefig(
        output_dir.joinpath(f"words_filter.{format}"), backend="pgf", **save_args
    )


if __name__ == "__main__":
    main()
