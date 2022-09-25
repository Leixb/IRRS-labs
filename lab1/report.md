---
title: |
    ![](./images/logo-upc-fib.pdf)
    ElasticSearch and Zipf's and Heaps' laws
subtitle: Information Retrieval and Recommender systems
author:
- Aleix Boné
- Albert Pita
date: September 2022
geometry: margin=1in
papersize: a4
fontsize: 12pt
line-height: 1.5
header-includes: |
    \usepackage{booktabs}
    \usepackage{siunitx}
    \usepackage{pdfpages}
    \usepackage{pdflscape}
    \usepackage{float}
    \makeatletter
    \def\fps@figure{H}
    \makeatother
    \usepackage[justification=centering]{caption}
    \makeatletter
    \g@addto@macro\@floatboxreset\centering
    \makeatother
    \setkeys{Gin}{width=0.7\linewidth}
    \usepackage{varioref}
    \usepackage{cleveref}
    \hypersetup{
        colorlinks = true,
        linkcolor={black},
        citecolor={black},
        urlcolor={blue!80!black}
    }
---

\pagenumbering{gobble}
\pagebreak
\pagenumbering{arabic}
# *Proper* words filtering {#proper-words-filtering .unnumbered}

In this practice the main objectives are to test both Zipfs' and Heaps'
law. However, before that, we are asked to filter the document
containing all the words of a large set of texts by leaving only the
appropriate words. This section describes this filtering.

Basically for this we have used the [`isalpha()`](https://docs.python.org/3/library/stdtypes.html#str.isalpha) function, which returns
true if all characters of a string are alphabets. We consider this
enough to perform the experiments, since it eliminates the numbers,
binary, urls, dates or not very readable things. even so, if we wanted
to be stricter we could use the [_enchant_](https://pyenchant.github.io/pyenchant/) library to check if each term
is in the English dictionary and if not erase it.

# Zipf's law {#zipfs-law .unnumbered}

As mentioned above, one of the main objectives of this practice is the
verification of Zipf's law of rank-frequency for a set of large texts
previously indexed and filtered. In particular, we want to see if the
following law holds:

\begin{equation}\label{eq:zipf}
    f = c*(rank+b)^{-a}
\end{equation}

For this purpose, the parameters $a$, $b$ and $c$ of the equation must be
determined to achieve an optimal fit to the empirical data extracted
from the previously mentioned files.

The [`curve_fit`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.curve_fit.html) function, from the [`scipy` library](https://docs.scipy.org), has been
used to adjust the functions. This function takes as arguments the
function to optimize, the data for the $x$ and the data for the $y$ and
returns a list with the optimal values for the parameters of the
function.

Initially, an attempt was made to execute the function by passing the
parameters *a*, *b* and *c* without any further specification. The
results obtained by doing so can be seen in \cref{fig:zip_init}

![Initial Zipf fit (Log-log scale)](./figures/zipf_naive_loglog.pdf){#fig:zip_init}

The double-logarithmic graph shows a double straight line which does not
fit at all to the empirical data observed. Therefore, we can see that
the values obtained (${a\approx0.3,}\, {b\approx -1},\, {c\approx 1300}$) are not good and further adjustments have to be made.

To make these adjustments, we have looked at the zipfs law itself and
how the parameters *a*, *b* and *c* act on it. We have seen that, for
example if *b* is -1 a division by 0 can occur, or if *a* is negative,
then instead of a decreasing function it becomes an increasing one,
which in the context we are in, makes no sense, as per definitions low
ranks should be the ones with higher frequencies. Also, we have observed
that if *c* is negative, then the whole expression becomes negative and
as a result it would give a negative frequency, which again makes no
sense.

With all this information, we have tried to put a lower boundary to the
optimizer in order to help it to achieve better results. We have set to
0 for all the parameters, so they can not be negative. Additionally, we
ignored the first 10 values when performing the fit. With this improvements we
have obtained the results shown in \cref{fig:zipf_bound}:

![Zipf fit with boundaries (Log-log
scale)](./figures/zipf_bounded_skip_10_loglog.pdf){#fig:zipf_bound}

As can be seen, with values a = 9.91144198e-01, b = 1.31458095e+00 and c
= 5.51413686e+05, the two graphs fit the empirical data almost
perfectly. The most noticeable difference being in the tail. We are not
clear why it happens, but we think it is because we have to adjust the
limits more. Thus, we can say that the range-frequency distribution
follows Zipf's function.

# Heap's law {#heaps-law .unnumbered}

The other main objective of this session was to test Heaps' law. This
law aims to calculate the number of different words that can appear in a
document. It has the following formula:

\begin{equation}\label{eq:heaps}
V = k \cdot N^\beta
\end{equation}

Where *V* represents the number of different words (vocabulary), *N* the document
size and *k* and $\beta$ the parameters to be determined from the
function setting.

In this practice, we will seek to obtain the optimal values for the
parameters *k* and $\beta$ to later compare the function with the
empirical results obtained from the word count and their respective
frequencies extracted from the previously mentioned files.

## Data collection

Since \emph{ElasticSearch} does not provide a built-in method to compute the
number of different words in a text, we opted to use traditional methods
using \texttt{POSIX} tools. For this, we developed a bash script that
for each novel, splits it into 100 pieces (linewise) and then computes
the number of unique and total words for piece 1, then for pieces 1 and 2
together and so on. The result is a cumulative data of the number of unique
words for each document.

## Analysis and results

Once again, we will use 
the `curve_fit` function of
the `scipy.optimize` library, to optimize the $k$ and $\beta$ parameters of
Heaps' law (\cref{eq:heaps})

Using our method, be obtained data from all 33 novels, here we will only discuss
2 which we found interesting, the rest of the plots can be found in the
appendix or in the \textit{figures} folder of the deliverable.

One thing we came upon when analyzing the data, was that all novels contained
a Project Gutenberg's legal notice at the end of approximately 3000 words. This
was quite noticeable in the plots as we'll show, specially for short novels.
To mitigate the effect of the legal terms, we performed the fit ignoring the
last 3 thousand words.

In \cref{fig:darwin} we can see how the for that particular novel does
follow Heaps' law. In general, all the novels we analyzed adhered to the law.

\vspace{-1em}

\begin{figure}[H]
\includegraphics[page=2]{figures/heaps}
\caption{Herdan-Heaps results obtained for Darwin's \emph{On the Origin of Species}}
\label{fig:darwin}
\end{figure}

Another example with a smaller novel can be seen in \cref{fig:kipling}.
The Gutenberg projects legal notice is quite more noticeable in this as we
can clearly see how the last 3000 words introduce vocabulary at a much higher
rate.

\begin{figure}[H]
\includegraphics[page=6]{figures/heaps}
\caption{Kipling}
\label{fig:kipling}
\end{figure}

\Cref{fig:heaps_all} shows the heaps curves for all the novels together. We can see that all
the models follow a similar trend, with only 2 or 3 outliers: *On the
origins of Species* by Charles Darwin with $\beta=0.45$ and *The English
novel in the time of Shakespeare* by J.J. Jusserand with a $\beta=0.63$.
Nonetheless, all the values fit inside the expected range for English
for Heaps law: $0.4 < \beta < 0.6$ and $10 < k < 100$ (except the aforementioned
novel by Jusserand), we can conclude that Heaps' law holds for our data.

![Heaps](figures/heaps_all.pdf){#fig:heaps_all}

Interestingly, for some similarly short novels, the legal terms where
not noticeable, probably because they talked of the setting of the novel.
We speculate that more technical ones it does not affect so much, while in
the fantasy ones or even in the older ones that do not have a modern
language less. This is because the vocabulary in the former tends to be
common, while in the latter it is not.

\pagebreak
\appendix
\section{Appendix}\label{sec:appendix}

\begin{table}[ht]
\centering
\caption{Heaps fits data}%
\label{tab:heaps}
\resizebox{\textwidth}{!}{
\input{./tables/heaps.tex}
}
\end{table}

\includepdf[pages=-,fitpaper]{figures/heaps.pdf}

