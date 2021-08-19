#!/bin/zsh

export MAXVOTES=2

export CLASSIFIERS="1 2"
./score-context-attributes-kernel.sh

export CLASSIFIERS="2 6"
./score-context-attributes-kernel.sh

export CLASSIFIERS="3 6"
./score-context-attributes-kernel.sh

export CLASSIFIERS="4 6"
./score-context-attributes-kernel.sh

export CLASSIFIERS="5 6"
./score-context-attributes-kernel.sh

export CLASSIFIERS="6 7"
./score-context-attributes-kernel.sh

export CLASSIFIERS="6 8"
./score-context-attributes-kernel.sh

export CLASSIFIERS="6 9"
./score-context-attributes-kernel.sh

export CLASSIFIERS="6 10"
./score-context-attributes-kernel.sh

