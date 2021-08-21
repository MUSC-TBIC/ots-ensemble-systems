#!/bin/bash

#############################################
## All 17 (n) classifiers
export MAXVOTES=17

export CLASSIFIERS="1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17"
./score-context-attributes-kernel.sh

#############################################
## 2 (n-15) classifiers
export MAXVOTES=2

export CLASSIFIERS="1 14"
./score-context-attributes-kernel.sh

export CLASSIFIERS="2 14"
./score-context-attributes-kernel.sh

export CLASSIFIERS="3 14"
./score-context-attributes-kernel.sh

export CLASSIFIERS="4 14"
./score-context-attributes-kernel.sh

export CLASSIFIERS="5 14"
./score-context-attributes-kernel.sh

export CLASSIFIERS="6 14"
./score-context-attributes-kernel.sh

export CLASSIFIERS="7 14"
./score-context-attributes-kernel.sh

export CLASSIFIERS="8 14"
./score-context-attributes-kernel.sh

export CLASSIFIERS="9 14"
./score-context-attributes-kernel.sh

export CLASSIFIERS="10 14"
./score-context-attributes-kernel.sh

export CLASSIFIERS="11 14"
./score-context-attributes-kernel.sh

export CLASSIFIERS="12 14"
./score-context-attributes-kernel.sh

export CLASSIFIERS="13 14"
./score-context-attributes-kernel.sh

export CLASSIFIERS="14 15"
./score-context-attributes-kernel.sh

export CLASSIFIERS="14 16"
./score-context-attributes-kernel.sh

export CLASSIFIERS="14 17"
./score-context-attributes-kernel.sh
