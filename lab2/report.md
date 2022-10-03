---
title: |
    \includegraphics[width=\linewidth]{../common/logo-upc-fib.pdf}\vspace{2em}
    Lab Session 2: Programming with ElasticSearch
subtitle: Information Retrieval and Recommender systems
author:
- Aleix Boné
- Carol Azparrent
date: October 2022
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
    <!-- \setkeys{Gin}{width=0.8\linewidth} -->
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

# The index reloaded

## Tokenizers

\Cref{fig:words_token} shows the number of words obtained using no
filters in the _novels_ dataset when applying the different _tokenizers_
available in ElasticSearch. We can observe that \texttt{whitespace}
produces more than two times the number of words than the other tokenizers.

<!-- TODO: Why whitespace so much ??? -->

![Number of words obtained with different tokenizers](./figures/words_token.pdf){#fig:words_token}

## Filters

We tried all possible combinations of the 6 filters available, which
amounts to $2^6 = 64$ possibilities. To achieve that, we created a
\texttt{bash} script that run our program for each combination and
collected the relevant metrics. We collected, the number of unique
words as well as the top 10 most common words and their frequencies
for each combination.

\Cref{fig:words_filter} shows the results of the number of unique
words for all combinations of filters. The lowercase filter
is shown as the color of the bars since we found that it was the most
impactful one. We used the _standard_ tokenizer and the data
from `20_newsgroups`.

<!-- TODO: what can we conclude from the graph -->

![Number of unique words obtained with different filters](./figures/words_filter.pdf){#fig:words_filter}

<!-- TODO: zipf? -->

# Computing tf-idf's and cosine similarity

## Understanding the code

## Implementing new features

# Conclusions
