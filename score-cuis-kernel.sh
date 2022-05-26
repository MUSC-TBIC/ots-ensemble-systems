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

export TASK=2019_n2c2_track3

export N2C2_2019_DIR=/data/n2c2_corpora/2019_n2c2_track-3

## N2C2_2019_DIR
## |-- train
## |   |-- train_norm
## |   `-- train_note
## |-- test
## |   |-- test_norm
## |   |-- test_norm_cui_replaced_with_unk
## |   `-- test_note
## `-- top10_outputs
##     |-- submission_Ali.txt
##     |-- submission_KP.txt
##     |-- submission_MDQ.txt
##     |-- submission_MIT.txt
##     |-- submission_NaCT.txt
##     |-- submission_TTI.txt
##     |-- submission_UAZ.txt
##     |-- submission_UAv.txt
##     |-- submission_UWM.txt
##     `-- submission_ezDI.txt

export RESULT_DIR=/data/experiments/ots-ensemble-paper
export RESULT_FILE=${RESULT_DIR}/${TASK}/${TASK}_results.csv

## RESULT_DIR/2019_n2c2_track3
## |-- 2019_n2c2_track3_results.csv
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
    ${ENSEMBLE_DIR}/medspaCy/oracleEnsemble.py \
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
    --fuzzy-match-flags exact \
    --score-normalization note_nlp_source_concept_id \
    --metrics Accuracy TP FP FN TN \
    > ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${SAFE_CLASSIFIERS}.log

export COVERAGE=`grep micro ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${SAFE_CLASSIFIERS}.log | cut -f 2 | head -n 1 | tr '\n' '\t'`
export ACCURACY=`grep micro ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${SAFE_CLASSIFIERS}.log | cut -f 2 | tail -n 1 | tr '\n' '\t'`
    
echo "${METHOD}	${CLASSIFIERS}	${ACCURACY}${COVERAGE}${MINVOTES}	all" \
     >> ${RESULT_FILE}


export METHOD=decisionTemplate
export MODEL_DIR=${RESULT_DIR}/${TASK}/${METHOD}-models
export MINVOTES=1
## TODO - We don't use thresholding for decision templates yet
for MINTHRESHOLD in 0.0
do
    export SYS_DIR=${RESULT_DIR}/${TASK}/${METHOD}/${MINVOTES}_${SAFE_CLASSIFIERS}
    export SYS_TRAIN_DIR=${RESULT_DIR}/${TASK}/${METHOD}/${MINVOTES}_${SAFE_CLASSIFIERS}/train
    export SYS_TEST_DIR=${RESULT_DIR}/${TASK}/${METHOD}/${MINVOTES}_${SAFE_CLASSIFIERS}/test
    mkdir -p ${SYS_DIR}
    mkdir -p ${SYS_TRAIN_DIR}
    mkdir -p ${SYS_TEST_DIR}

    ## Train Decision Template ensemble system
    ${ENSEMBLE_CONDA}/bin/python3 \
            ${ENSEMBLE_DIR}/medspaCy/decisionTemplate.py \
            --types-dir ${ENSEMBLE_DIR}/types \
            --phase train \
            --voting-unit span \
            --input-dir "${MERGED_OUT}" \
            --classifier-list ${CLASSIFIERS} \
            --overlap-strategy rank \
            --zero-strategy drop \
            --decision-profiles-file "${MODEL_DIR}/${MINVOTES}_${SAFE_CLASSIFIERS}.pkl"

    ## Test Decision Template ensemble system
    ${ENSEMBLE_CONDA}/bin/python3 \
            ${ENSEMBLE_DIR}/medspaCy/decisionTemplate.py \
            --types-dir ${ENSEMBLE_DIR}/types \
            --phase test \
            --voting-unit span \
            --input-dir "${MERGED_OUT}" \
            --classifier-list ${CLASSIFIERS} \
            --overlap-strategy rank \
            --zero-strategy drop \
            --decision-profiles-file "${MODEL_DIR}/${MINVOTES}_${SAFE_CLASSIFIERS}.pkl" \
            --output-dir ${SYS_DIR}

    ${ETUDE_CONDA}/bin/python3 ${ETUDE_DIR}/etude.py \
      --reference-conf ${CONFIG_DIR}/uima/ensemble_note-nlp_xmi.conf \
      --reference-input ${REF_DIR} \
      --test-conf ${CONFIG_DIR}/uima/ensemble_note-nlp_xmi.conf \
      --test-input ${SYS_TRAIN_DIR} \
      --file-suffix ".xmi" \
      --fuzzy-match-flags exact \
      --score-normalization note_nlp_source_concept_id \
      --metrics Accuracy TP FP FN TN \
      > ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${SAFE_CLASSIFIERS}_train.log

    export COVERAGE=`grep micro ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${SAFE_CLASSIFIERS}_train.log | cut -f 2 | head -n 1 | tr '\n' '\t'`
    export ACCURACY=`grep micro ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${SAFE_CLASSIFIERS}_train.log | cut -f 2 | tail -n 1 | tr '\n' '\t'`
    
    echo "${METHOD}	${CLASSIFIERS}	${ACCURACY}${COVERAGE}${MINVOTES}	trn" \
        >> ${RESULT_FILE}

    ${ETUDE_CONDA}/bin/python3 ${ETUDE_DIR}/etude.py \
      --reference-conf ${CONFIG_DIR}/uima/ensemble_note-nlp_xmi.conf \
      --reference-input ${REF_DIR} \
      --test-conf ${CONFIG_DIR}/uima/ensemble_note-nlp_xmi.conf \
      --test-input ${SYS_TEST_DIR} \
      --file-suffix ".xmi" \
      --fuzzy-match-flags exact \
      --score-normalization note_nlp_source_concept_id \
      --metrics Accuracy TP FP FN TN \
      > ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${SAFE_CLASSIFIERS}_test.log

    export COVERAGE=`grep micro ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${SAFE_CLASSIFIERS}_test.log | cut -f 2 | head -n 1 | tr '\n' '\t'`
    export ACCURACY=`grep micro ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${SAFE_CLASSIFIERS}_test.log | cut -f 2 | tail -n 1 | tr '\n' '\t'`
    
    echo "${METHOD}	${CLASSIFIERS}	${ACCURACY}${COVERAGE}${MINVOTES}	tst" \
        >> ${RESULT_FILE}
done



export METHOD=voting
for MINVOTES in $(seq 1 ${MAXVOTES})
do

    export SYS_DIR=${RESULT_DIR}/${TASK}/${METHOD}/${MINVOTES}_${SAFE_CLASSIFIERS}
    mkdir -p ${SYS_DIR}
    
    ## Simple voting ensemble system
    ${ENSEMBLE_CONDA}/bin/python3 \
        ${ENSEMBLE_DIR}/medspaCy/votingEnsemble.py \
        --types-dir ${ENSEMBLE_DIR}/types \
        --input-dir "${MERGED_OUT}" \
        --voting-unit span \
        --classifier-list ${CLASSIFIERS} \
        --min-votes ${MINVOTES} \
        --overlap-strategy rank \
        --rank-file ${RESULT_DIR}/${TASK}/rankedClassifiersTop-voting.csv \
        --zero-strategy drop \
        --output-dir ${SYS_DIR}

    ${ETUDE_CONDA}/bin/python3 ${ETUDE_DIR}/etude.py \
      --reference-conf ${CONFIG_DIR}/uima/ensemble_note-nlp_xmi.conf \
      --reference-input ${REF_DIR} \
      --test-conf ${CONFIG_DIR}/uima/ensemble_note-nlp_xmi.conf \
      --test-input ${SYS_DIR} \
      --file-suffix ".xmi" \
      --fuzzy-match-flags exact \
      --score-normalization note_nlp_source_concept_id \
      --metrics Accuracy TP FP FN TN \
      > ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${SAFE_CLASSIFIERS}.log

    export COVERAGE=`grep micro ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${SAFE_CLASSIFIERS}.log | cut -f 2 | head -n 1 | tr '\n' '\t'`
    export ACCURACY=`grep micro ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${SAFE_CLASSIFIERS}.log | cut -f 2 | tail -n 1 | tr '\n' '\t'`
    
    echo "${METHOD}	${CLASSIFIERS}	${ACCURACY}${COVERAGE}${MINVOTES}	all" \
        >> ${RESULT_FILE}
done
