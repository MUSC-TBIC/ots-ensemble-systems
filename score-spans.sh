#!/bin/bash

#############################################
## All 10 (n) classifiers
export MAXVOTES=10

export CLASSIFIERS="1 2 3 4 5 6 7 8 9 10"
./score-spans-kernel.sh

#############################################
## 2 (n-8) classifiers
export MAXVOTES=2

export CLASSIFIERS="1 5"
./score-spans-kernel.sh

export CLASSIFIERS="2 5"
./score-spans-kernel.sh

export CLASSIFIERS="3 5"
./score-spans-kernel.sh

export CLASSIFIERS="4 5"
./score-spans-kernel.sh

export CLASSIFIERS="5 6"
./score-spans-kernel.sh

export CLASSIFIERS="5 7"
./score-spans-kernel.sh

export CLASSIFIERS="5 8"
./score-spans-kernel.sh

export CLASSIFIERS="5 9"
./score-spans-kernel.sh

export CLASSIFIERS="5 10"
./score-spans-kernel.sh
