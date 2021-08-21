#!/bin/bash

if [[ -z $CLASSIFIERS ]]; then
    echo "The variable \$CLASSIFIERS is not set"
    exit 0
fi
export SAFE_CLASSIFIERS=`echo $CLASSIFIERS | tr ' ' 'x'`

if [[ -z $MAXVOTES ]]; then
    echo "The variable \$MAXVOTES is not set"
    exit 0
fi

## Most, if not all, of these environment variables will need to be
## customized to match your running environment.
export ENSEMBLE_DIR=/data/software/ots-ensemble-systems
export ENSEMBLE_CONDA=/data/software/anaconda3/envs/ensemble-py3.8
export ETUDE_DIR=/data/software/etude
export ETUDE_CONDA=/data/software/anaconda3/envs/etude
export CONFIG_DIR=/data/software/etude-engine-configs

export TASK=2009_i2b2_medications

export I2B2_2009_DIR=/data/i2b2_corpora/2009_i2b2_challenge_medications

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

export RESULT_DIR=/data/experiments/ots-ensemble-paper
export RESULT_FILE=${RESULT_DIR}/${TASK}/${TASK}_results.csv

## RESULT_DIR/2009_i2b2_medications
## |-- 2009_i2b2_medications_results.csv
## |-- rankedClassifiersTop.csv
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
export REF_DIR=${RESULT_DIR}/${TASK}/ref

export METHOD=oracle
export SYS_DIR=${RESULT_DIR}/${TASK}/${METHOD}/${SAFE_CLASSIFIERS}
mkdir -p ${SYS_DIR}

export MINVOTES=1

## Create an oracle of best possible output
${ENSEMBLE_CONDA}/bin/python3 \
    ${ENSEMBLE_DIR}/medspaCy/oracle-ensemble.py \
    --types-dir ${ENSEMBLE_DIR}/types \
    --input-dir "${MERGED_OUT}" \
    --classifier-list ${CLASSIFIERS} \
    --voting-unit span \
    --output-dir ${SYS_DIR}

${ETUDE_CONDA}/bin/python3 ${ETUDE_DIR}/etude.py \
    --reference-conf ${CONFIG_DIR}/uima/ensemble_note-nlp_xmi.conf \
    --reference-input ${REF_DIR} \
    --test-conf ${CONFIG_DIR}/uima/ensemble_note-nlp_xmi.conf \
    --test-input ${SYS_DIR} \
    --file-suffix ".xmi" \
    --fuzzy-match-flags exact partial \
    --metrics TP FP FN TN Recall Precision F1 \
    > ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${SAFE_CLASSIFIERS}.log

export EXACT_RECPRECF1=`grep micro ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${SAFE_CLASSIFIERS}.log | cut -f 6- | head -n 1 | tr '\n' '\t'`
export PARTIAL_RECPRECF1=`grep micro ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${SAFE_CLASSIFIERS}.log | cut -f 6- | tail -n 1 | tr '\n' '\t'`
    
echo "${METHOD}	${CLASSIFIERS}	Exact	${EXACT_RECPRECF1}${MINVOTES}" \
     >> ${RESULT_FILE}
echo "${METHOD}	${CLASSIFIERS}	Partial	${PARTIAL_RECPRECF1}${MINVOTES}" \
     >> ${RESULT_FILE}

export METHOD=voting
for MINVOTES in $(seq 1 ${MAXVOTES})
do

    export SYS_DIR=${RESULT_DIR}/${TASK}/${METHOD}/${MINVOTES}_${SAFE_CLASSIFIERS}
    mkdir -p ${SYS_DIR}
    
    ## Simple voting ensemble system
    ${ENSEMBLE_CONDA}/bin/python3 \
        ${ENSEMBLE_DIR}/medspaCy/voting-ensemble.py \
        --types-dir ${ENSEMBLE_DIR}/types \
        --input-dir "${MERGED_OUT}" \
        --voting-unit span \
        --classifier-list ${CLASSIFIERS} \
        --min-votes ${MINVOTES} \
        --overlap-strategy rank \
        --rank-file ${RESULT_DIR}/${TASK}/rankedClassifiersTop.csv \
        --zero-strategy drop \
        --output-dir ${SYS_DIR}
    
    ${ETUDE_CONDA}/bin/python3 ${ETUDE_DIR}/etude.py \
      --reference-conf ${CONFIG_DIR}/uima/ensemble_note-nlp_xmi.conf \
      --reference-input ${REF_DIR} \
      --test-conf ${CONFIG_DIR}/uima/ensemble_note-nlp_xmi.conf \
      --test-input ${SYS_DIR} \
      --file-suffix ".xmi" \
      --fuzzy-match-flags exact partial \
      --metrics TP FP FN TN Recall Precision F1 \
      > ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${SAFE_CLASSIFIERS}.log
    
    export EXACT_RECPRECF1=`grep micro ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${SAFE_CLASSIFIERS}.log | cut -f 6- | head -n 1 | tr '\n' '\t'`
    export PARTIAL_RECPRECF1=`grep micro ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${SAFE_CLASSIFIERS}.log | cut -f 6- | tail -n 1 | tr '\n' '\t'`
    
    echo "${METHOD}	${CLASSIFIERS}	Exact	${EXACT_RECPRECF1}${MINVOTES}" \
      >> ${RESULT_FILE}
    echo "${METHOD}	${CLASSIFIERS}	Partial	${PARTIAL_RECPRECF1}${MINVOTES}" \
      >> ${RESULT_FILE}
done
