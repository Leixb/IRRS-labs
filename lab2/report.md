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

### Optimizing the code for parallelism

When taking a closer look to the code, we realized that there mas no form
of parallelism. Given that some the computations are embarrassingly
parallel, we decided to optimize the codebase so that we could run our
experiments faster. Here are the changes we made and the measured
speedups on the `arxiv` dataset:

- `IndexFilesPreprocess.py`
    - We changed the `ldocs` and `generate_files_list` to work as generators.
      This prevents unnecessarily allocating all the documents on memory.
    - Use `bulk_parallel` instead of `bulk` to perform the indexing.
    - Speedup: **22.3s \textrightarrow{} 5.6s (74%)**
    - Memory usage: 165Mb \textrightarrow{} 37Mb
- `CountWords.py`
    - We used `elasticsearch-dsl` sliced scan to slice the query results and
    process them in separate threads.
    - Instead of manually iterating and building our counter dictionary, we
    used `collections.Counter`. This provides 2 benefits:
        1. We can merge the `Counter` from each thread result efficiently and
           without writing any code.
            - Note: The combination of results is performed sequentially but could be
            improved by implementing it as a parallel reduce.
        2. We can get the number of words and unique words, instantly as well
        as getting the $n$ most common words computed using an efficient heap.
        - For cases where 
    - Speedup: **37.2s \textrightarrow 7.1s (81%)**

These results highly depend on the hardware where the computations are
performed, in our case a 6 core machine with 2 threads per core, running
both the ElasticSearch server and the python scripts. However, the benefits
are quite significant, with an overall speedup of more than 75%.

The parallel versions of the scripts are available in the delivery as
`IndexFilesPreprocess_par.py` and `CountWords_par.py`.

<!-- ## Implementing new features -->

<!-- - `CountWords.py` -->
<!--     - Add option to only compute top $n$ most common -->
<!--         - This reduces execution time and memory usage by using a heap queue -->
<!-- - `IndexFilesPreprocess.py` -->
<!-- - `TFIDFViewer.py` -->

# Conclusions
