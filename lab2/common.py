from typing import Dict

import seaborn as sns


def set_theme() -> Dict:
    sns.set_theme(
        context="paper",
        style="whitegrid",
        font_scale=1.5,
        font="STIXGeneral",
        rc={
            "text.usetex": True,
            "text.latex.preamble": r"\usepackage{color}\usepackage{xcolor}",
            "pgf.rcfonts": False,  # Ignore Matplotlibrc
            # "pgf.rcfonts": True,  # Ignore Matplotlibrc
            "pgf.preamble": "\n".join(
                [r"\usepackage{color}" r"\usepackage{xcolor}"]  # xcolor for colours
            ),
            "font.serif": [],
            "font.family": "serif",
        },
    )
    return {"dpi": 300}
