#!/bin/zsh

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

export CLASSIFIERS="6 0"
./score-cuis-kernel.sh
