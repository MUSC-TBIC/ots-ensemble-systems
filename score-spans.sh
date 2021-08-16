#!/bin/zsh

export MAXVOTES=2

export CLASSIFIERS=12
./score-spans-kernel.sh

export CLASSIFIERS=26
./score-spans-kernel.sh

export CLASSIFIERS=36
./score-spans-kernel.sh

export CLASSIFIERS=46
./score-spans-kernel.sh

export CLASSIFIERS=56
./score-spans-kernel.sh

export CLASSIFIERS=67
./score-spans-kernel.sh

export CLASSIFIERS=68
./score-spans-kernel.sh

export CLASSIFIERS=69
./score-spans-kernel.sh

export CLASSIFIERS=60
./score-spans-kernel.sh

