#!/bin/zsh

## Most, if not all, of these environment variables will need to be
## customized to match your running environment.
export SECTIONIZER_DIR=/Users/pmh/git/ots-clinical-sectionizer
export SECTIONIZER_CONDA=~/opt/anaconda3/envs/sections-py3.8
export ENSEMBLE_DIR=/Users/pmh/git/ots-ensemble-systems
export ENSEMBLE_CONDA=~/opt/anaconda3/envs/ensemble-py3.8
export ETUDE_DIR=/Users/pmh/git/etude
export ETUDE_CONDA=~/opt/anaconda3/envs/etude-py3.7
export CONFIG_DIR=/Users/pmh/git/etude-engine-configs

export TASK=2009_i2b2_medications

export I2B2_2009_DIR=/Users/pmh/data/i2b2_corpora/2009_i2b2_challenge_medications

## I2B2_2008_DIR
## |-- obesity_annotations_test.xml
## |-- obesity_annotations_training.xml
## |-- obesity_annotations_training2.xml
## |-- obesity_corpus_test.xml
## |-- obesity_corpus_training.xml
## |-- obesity_corpus_training2.xml
## `-- team_submissions/top_subs
##     |-- prod_123_0_1_nlpoa00WJ
##     |-- prod_190_0_1_nlpQF1X7H
##     `-- prod_204_0_3_nlpB1l4ZH

export RESULT_DIR=/Users/pmh/git/ots-ensemble-systems/data/out
export RESULT_FILE=${RESULT_DIR}/${TASK}/${TASK}_results.csv

## RESULT_DIR/2009_i2b2_medications
## |-- 2009_i2b2_medications_results.csv
## |-- etude
## |   |-- voting_1_1.log
## |   |-- voting_1_2.log
## |   |-- voting_1_3.log
## |   |-- ...
## |   |-- voting_1_123.log
## |   |-- ...
## |   |-- voting_2_123.log
## |   |-- ...
## |   `-- voting_3_123.log
## `-- merged
## |   |-- consolidated.xmi
## |   |-- ...
## |   `-- files.xmi
## `-- voting
##     |-- processed.xmi
##     |-- ...
##     `-- files.xmi

export MERGED_OUT=${RESULT_DIR}/${TASK}/merged
mkdir -p "${MERGED_OUT}"

mkdir -p ${RESULT_DIR}/${TASK}/etude

export METHOD=voting
export SYS_DIR=${RESULT_DIR}/${TASK}/${METHOD}
mkdir -p ${SYS_DIR}

## Merge the oracle/reference annotation with the above classifiers to
## generate a single input corpus for the meta-classifier ensemble
## system to read in
${ENSEMBLE_CONDA}/bin/python3 \
    ${ENSEMBLE_DIR}/medspaCy/i2b2-2009-medications-converter.py \
    --input-text ${I2B2_2009_DIR}/test_corpus \
    --input-ref ${I2B2_2009_DIR}/test_annotations/converted.noduplicates.sorted \
    --input-systems ${I2B2_2009_DIR}/team_submissions/top_subs \
    --output-dir ${MERGED_OUT}

export METHOD=voting
export MINVOTES=1
for CLASSIFIERS in {1..2}
do
    export SYS_DIR=${RESULT_DIR}/${TASK}/${METHOD}/${MINVOTES}_${CLASSIFIERS}
    mkdir -p ${SYS_DIR}

    ## Simple voting ensemble system
    ${ENSEMBLE_CONDA}/bin/python3 \
        ${ENSEMBLE_DIR}/medspaCy/voting-ensemble.py \
        --types-dir /Users/pmh/git/ots-ensemble-systems/types \
        --input-dir "${MERGED_OUT}" \
        --voting-unit span \
        --classifier-list ${CLASSIFIERS} \
        --min-vote ${MINVOTES} \
        --overlap-strategy rank \
        --zero-strategy drop \
        --output-dir ${SYS_DIR}
done
