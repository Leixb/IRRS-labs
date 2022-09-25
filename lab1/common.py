from typing import Callable, Dict, Tuple

import numpy as np
import numpy.typing as npt
import seaborn as sns
from scipy.optimize import curve_fit


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


def RMSE(y: npt.NDArray, y_fit: npt.NDArray) -> float:
    return np.sqrt(np.mean(np.power(y - y_fit, 2)))


def R2(y: npt.NDArray, y_fit: npt.NDArray) -> float:
    y_mean = np.mean(y)
    ss_tot = np.sum(np.power(y - y_mean, 2))
    ss_res = np.sum(np.power(y - y_fit, 2))

    return 1 - ss_res / ss_tot


def set_theme() -> Dict:
    sns.set_theme(
        context="paper",
        style="whitegrid",
        font_scale=1.5,
        font="STIXGeneral",
        rc={
            "text.usetex": True,
        },
    )
    return {"dpi": 300}
