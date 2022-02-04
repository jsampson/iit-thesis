#!/bin/bash

set -e

for prog in pqr counter pqrpqr optimized unrolled; do
    echo "============================"
    echo "$prog - program"
    echo "----------------------------"
    cat $prog.txt
    echo "============================"
    echo "$prog - analysis"
    echo "----------------------------"
    docker run -it --rm --pull never iit-thesis $prog.txt phi
    echo "============================"
    echo "$prog - causal model"
    echo "----------------------------"
    docker run -it --rm --pull never iit-thesis $prog.txt micro
done
