#!/bin/zsh

export MAXVOTES=2

export CLASSIFIERS=16
./score-cuis-kernel.sh

export CLASSIFIERS=26
./score-cuis-kernel.sh

export CLASSIFIERS=36
./score-cuis-kernel.sh

export CLASSIFIERS=46
./score-cuis-kernel.sh

export CLASSIFIERS=56
./score-cuis-kernel.sh

export CLASSIFIERS=67
./score-cuis-kernel.sh

export CLASSIFIERS=68
./score-cuis-kernel.sh

export CLASSIFIERS=69
./score-cuis-kernel.sh

export CLASSIFIERS=60
./score-cuis-kernel.sh

