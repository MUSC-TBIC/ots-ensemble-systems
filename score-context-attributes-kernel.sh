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

export TASK=2008_i2b2_obesity

export I2B2_2008_DIR=/data/i2b2_corpora/2008_i2b2_challenge_obesity

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

## RESULT_DIR/2008_i2b2_obesity
## |-- 2008_i2b2_obesity_results.csv
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
    --voting-unit doc \
    --output-dir ${SYS_DIR}

${ETUDE_CONDA}/bin/python3 ${ETUDE_DIR}/etude.py \
    --reference-conf ${CONFIG_DIR}/i2b2/i2b2-2008-obesity_doc-level_note-nlp.conf \
    --reference-input ${REF_DIR} \
    --test-conf ${CONFIG_DIR}/i2b2/i2b2-2008-obesity_doc-level_note-nlp.conf \
    --test-input ${SYS_DIR} \
    --file-suffix ".xmi" \
    --fuzzy-match-flags doc-property \
    --metrics TP FP FN TN \
    --by-type \
    > ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${SAFE_CLASSIFIERS}.log

${ETUDE_CONDA}/bin/python3 ${ETUDE_DIR}/etude.py \
    --reference-conf ${CONFIG_DIR}/i2b2/i2b2-2008-obesity_doc-level_note-nlp.conf \
    --reference-input ${REF_DIR} \
    --test-conf ${CONFIG_DIR}/i2b2/i2b2-2008-obesity_doc-level_note-nlp.conf \
    --test-input ${SYS_DIR} \
    --file-suffix ".xmi" \
    --fuzzy-match-flags doc-property \
    --metrics TP FP FN TN \
    --by-type \
    --score-key Parent \
    >> ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${SAFE_CLASSIFIERS}.log

for i in `egrep -v "^(micro|macro|exact|doc-property)" ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${SAFE_CLASSIFIERS}.log | tr '\t' '|'`;do
    echo "${METHOD}	${CLASSIFIERS}	`echo $i | tr '|' '\t'`	${MINVOTES}" \
	 >> ${RESULT_FILE};done


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
        --voting-unit doc \
        --classifier-list ${CLASSIFIERS} \
        --min-votes ${MINVOTES} \
        --zero-strategy drop \
        --output-dir ${SYS_DIR}

    ${ETUDE_CONDA}/bin/python3 ${ETUDE_DIR}/etude.py \
      --reference-conf ${CONFIG_DIR}/i2b2/i2b2-2008-obesity_doc-level_note-nlp.conf \
      --reference-input ${REF_DIR} \
      --test-conf ${CONFIG_DIR}/i2b2/i2b2-2008-obesity_doc-level_note-nlp.conf \
      --test-input ${SYS_DIR} \
      --file-suffix ".xmi" \
      --fuzzy-match-flags doc-property \
      --metrics TP FP FN TN \
      --by-type \
      > ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${SAFE_CLASSIFIERS}.log

    ${ETUDE_CONDA}/bin/python3 ${ETUDE_DIR}/etude.py \
      --reference-conf ${CONFIG_DIR}/i2b2/i2b2-2008-obesity_doc-level_note-nlp.conf \
      --reference-input ${REF_DIR} \
      --test-conf ${CONFIG_DIR}/i2b2/i2b2-2008-obesity_doc-level_note-nlp.conf \
      --test-input ${SYS_DIR} \
      --file-suffix ".xmi" \
      --fuzzy-match-flags doc-property \
      --metrics TP FP FN TN \
      --by-type \
      --score-key Parent \
      >> ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${SAFE_CLASSIFIERS}.log

    for i in `egrep -v "^(micro|macro|exact|doc-property)" ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${SAFE_CLASSIFIERS}.log | tr '\t' '|'`;do
	echo "${METHOD}	${CLASSIFIERS}	`echo $i | tr '|' '\t'`	${MINVOTES}" \
	>> ${RESULT_FILE};done

done
