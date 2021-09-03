#!/bin/bash

#############################################
## All 10 (n) classifiers
export MAXVOTES=10

export CLASSIFIERS="1 2 3 4 5 6 7 8 9 10"
./score-cuis-kernel.sh

#############################################
## 9 (n-1) classifiers
export MAXVOTES=9

export CLASSIFIERS="2 3 4 5 6 7 8 9 10"
./score-cuis-kernel.sh

export CLASSIFIERS="1 3 4 5 6 7 8 9 10"
./score-cuis-kernel.sh

export CLASSIFIERS="1 2 4 5 6 7 8 9 10"
./score-cuis-kernel.sh

export CLASSIFIERS="1 2 3 5 6 7 8 9 10"
./score-cuis-kernel.sh

export CLASSIFIERS="1 2 3 4 6 7 8 9 10"
./score-cuis-kernel.sh

export CLASSIFIERS="1 2 3 4 5 7 8 9 10"
./score-cuis-kernel.sh

export CLASSIFIERS="1 2 3 4 5 6 8 9 10"
./score-cuis-kernel.sh

export CLASSIFIERS="1 2 3 4 5 6 7 9 10"
./score-cuis-kernel.sh

export CLASSIFIERS="1 2 3 4 5 6 7 8 10"
./score-cuis-kernel.sh

export CLASSIFIERS="1 2 3 4 5 6 7 8 9"
./score-cuis-kernel.sh

#############################################
## 8 (n-2) classifiers
export MAXVOTES=8

export CLASSIFIERS="3 4 5 6 7 8 9 10"
./score-cuis-kernel.sh

export CLASSIFIERS="1 4 5 6 7 8 9 10"
./score-cuis-kernel.sh

export CLASSIFIERS="1 3 5 6 7 8 9 10"
./score-cuis-kernel.sh

export CLASSIFIERS="1 3 4 6 7 8 9 10"
./score-cuis-kernel.sh

export CLASSIFIERS="1 3 4 5 7 8 9 10"
./score-cuis-kernel.sh

export CLASSIFIERS="1 3 4 5 6 8 9 10"
./score-cuis-kernel.sh

export CLASSIFIERS="1 3 4 5 6 7 9 10"
./score-cuis-kernel.sh

export CLASSIFIERS="1 3 4 5 6 7 8 10"
./score-cuis-kernel.sh

export CLASSIFIERS="1 3 4 5 6 7 8 9"
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
