#!/usr/bin/env -S awk -f

# Process the output of "kmeans_cores.sh"
#
# This takes a list of files "kmeans_<n>.log" where <n> is the number of
# cores used. And produces a file with the execution time for each iteration.
#
# ./kmeans_ncores.awk kmeans_*.log > kmeans_ncores.csv

BEGIN {
    OFS = ",";
    print "ncores,repetition,iteration,time";
}

BEGINFILE {
    ncores = FILENAME;
    sub(".*_", "", ncores);
    sub(".log", "", ncores);
}

$1 == "REP" { rep = $2 }

$1 == "Iteration" { iter = $2 }

$1 == "Time=" {
    print ncores, iter, rep, $2
}
