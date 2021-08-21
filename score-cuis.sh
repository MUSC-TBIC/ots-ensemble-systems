#!/bin/bash

#############################################
## All 10 (n) classifiers
export MAXVOTES=10

export CLASSIFIERS="1 2 3 4 5 6 7 8 9 10"
./score-cuis-kernel.sh

#############################################
## 2 (n-8) classifiers
export MAXVOTES=2

export CLASSIFIERS="1 6"
./score-cuis-kernel.sh

export CLASSIFIERS="2 6"
./score-cuis-kernel.sh

export CLASSIFIERS="3 6"
./score-cuis-kernel.sh

export CLASSIFIERS="4 6"
./score-cuis-kernel.sh

export CLASSIFIERS="5 6"
./score-cuis-kernel.sh

export CLASSIFIERS="6 7"
./score-cuis-kernel.sh

export CLASSIFIERS="6 8"
./score-cuis-kernel.sh

export CLASSIFIERS="6 9"
./score-cuis-kernel.sh

export CLASSIFIERS="6 10"
./score-cuis-kernel.sh
