#!/usr/bin/env python3

import pathlib
from functools import partial
from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from common import set_theme


def add_source(fig: plt.Figure, source: str) -> None:
    source.replace("_", r"\_")
    fig.text(
        0.01,
        0.01,
        f" source: \\texttt{{{source}}}",
        ha="left",
        fontsize=8,
        color="gray",
    )


def plot_tokenizers(
    df: pd.DataFrame, y: str = "unique", source: Optional[str] = None
) -> plt.Figure:
    ax = df.plot.bar(
        x="token",
        y=y,
        rot=0,
        legend=False,
        ylabel=f"{y} words".capitalize(),
        xlabel="Tokenizer",
        figsize=(6.4, 2.8),
    )
    ax.xaxis.grid(False)
    ax.ticklabel_format(axis="y", style="sci", scilimits=(3, 3))

    # plt.ylim(0, 100e3)
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

    if source is not None:
        add_source(ax.get_figure(), source)

    return ax.get_figure()


def colorize(x: str, include_lowercase: bool = False) -> str:
    max_len = "asciifolding-stop-porter_stem-kstem-snowball"

    if include_lowercase:
        max_len = "lowercase-" + max_len

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


def plot_filters(
    df: pd.DataFrame, x: str = "unique", hue="lowercase", source: Optional[str] = None
) -> plt.Figure:
    # take only the ones which contain lowercase in filter column
    # replace nan with empty string
    dd = df.fillna("none")

    lowercase = hue == "lowercase"

    if lowercase:
        dd["lowercase"] = dd["filters"].str.startswith("lowercase").fillna(False)
        dd["filters"] = dd["filters"].str.removeprefix("lowercase-")
        dd["filters"] = dd["filters"].str.replace("lowercase", "none")

    dd["filters"] = dd["filters"].apply(
        partial(colorize, include_lowercase=not lowercase)
    )

    fig, ax = plt.subplots()
    sns.barplot(
        x=x,
        y="filters",
        hue=hue,
        data=dd,
        alpha=0.8,
        palette=["r", "g"] if lowercase else sns.color_palette(),
        ax=ax,
    )

    plt.xlabel(f"{x} words".capitalize())
    plt.ylabel("Filters")
    plt.legend(
        loc="lower left", title=hue.capitalize(), framealpha=1 if lowercase else 0.7
    )
    ax.yaxis.grid(False)
    ax.ticklabel_format(axis="x", style="sci", scilimits=(3, 3))

    left_adj = 0.5 if lowercase else 0.6
    fig.subplots_adjust(left=left_adj, top=0.98, right=0.98)
    plt.yticks(fontsize=8)

    plt.figtext(
        left_adj - 0.025,
        0.08,
        r"number of filters  $\;\nearrow$",
        ha="right",
        fontsize=8,
        color="b",
    )

    if source is not None:
        add_source(ax.get_figure(), source)

    return ax.get_figure()


def plot_tokenizers_summary(df: pd.DataFrame, output_dir: pathlib.Path) -> plt.Figure:
    fig, ax = plt.subplots(2, 1, sharex=True)

    sns.barplot(x="collection", y="unique", hue="token", data=df, ax=ax[0])
    sns.barplot(x="collection", y="total", hue="token", data=df, ax=ax[1])

    ax[0].set_ylabel("Unique words")
    ax[0].set_xlabel("")
    ax[1].set_ylabel("Total words")
    ax[1].set_xlabel("Collection")

    # disable legends
    ax[0].legend().set_visible(False)
    ax[1].legend().set_visible(False)
    lines_labels = [ax[0].get_legend_handles_labels()]
    lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]

    fig.subplots_adjust(top=0.80)

    for axis in ax:
        axis.ticklabel_format(axis="y", style="sci", scilimits=(6, 6))

    plt.figlegend(
        lines, labels, loc="upper center", ncol=4, frameon=False, title="Tokenizer"
    )

    return fig


def save_fig(fig: plt.Figure, output_dir: pathlib.Path, name: str, **save_args) -> None:
    output_file = output_dir.joinpath(name)
    fig.savefig(output_file, **save_args)
    print(output_file.name)


def main(
    results_dir="./results",
    output_dir="./figures",
    tables_dir="./tables",
    format="pdf",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    results_dir = pathlib.Path(results_dir)
    output_dir = pathlib.Path(output_dir)
    tables_dir = pathlib.Path(tables_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    save_args = set_theme()

    df_token_list: List[pd.DataFrame] = []
    # Tokenizers
    for token_data in results_dir.glob("tokenizers_*.csv"):
        name = token_data.stem.removeprefix("tokenizers_")

        df = pd.read_csv(token_data).sort_values("unique")
        df_token_list.append(df)

        for variable in ["total", "unique"]:
            fig = plot_tokenizers(df, y=variable, source=name)
            save_fig(
                fig, output_dir, f"tokenizers_{name}_{variable}.{format}", **save_args
            )

        df[["token", "unique", "total"]].set_index("token").style.format(
            precision=3
        ).to_latex(tables_dir.joinpath(f"tokenizers_{name}.tex"), hrules=True)

    df_tokens = pd.concat(df_token_list)

    fig = plot_tokenizers_summary(df_tokens, output_dir)
    save_fig(fig, output_dir, f"tokenizers_all.{format}", **save_args)

    df_tokens.set_index(["collection", "token"]).style.format(precision=3).to_latex(
        tables_dir.joinpath("tokenizers_all.tex"), hrules=True
    )

    df_filter_list: List[pd.DataFrame] = []
    # Filters
    for filter_data in results_dir.glob("filters_*.csv"):
        name = filter_data.stem.removeprefix("filters_")

        df = pd.read_csv(filter_data, sep=";")
        df_filter_list.append(df)

        for variable in ["unique", "total"]:
            fig = plot_filters(df.sort_values(variable), x=variable, source=name)
            save_fig(
                fig,
                output_dir,
                f"filters_{name}_{variable}.{format}",
                backend="pgf",
                **save_args,
            )

        df[["filters", "unique", "total"]].set_index("filters").style.format(
            precision=3
        ).to_latex(tables_dir.joinpath(f"filters_{name}.tex"), hrules=True)

    df_filters = pd.concat(df_filter_list)

    fig = plot_filters(
        df_filters.sort_values("unique"), x="unique", hue="source", source="all"
    )
    save_fig(
        fig, output_dir, f"filters_unique_all.{format}", backend="pgf", **save_args
    )

    fig = plot_filters(
        df_filters.sort_values("total"), x="total", hue="source", source="all"
    )
    save_fig(fig, output_dir, f"filters_total_all.{format}", backend="pgf", **save_args)

    df[["source", "filters", "unique", "total"]].set_index(
        ["source", "filters"]
    ).style.format(precision=3).to_latex(
        tables_dir.joinpath("filters_all.tex"), hrules=True
    )

    return df_tokens, df_filters


if __name__ == "__main__":
    main()
