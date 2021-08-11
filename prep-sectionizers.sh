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

export RESULT_DIR=/Users/pmh/git/ots-ensemble-systems/data/out3

export TASK=sectionizing

export RESULT_FILE=/Users/pmh/git/ots-ensemble-systems/data/out2/${TASK}/${TASK}_results.csv

export TEXTRACTOR_DIR='/Users/pmh/Box Sync/TBIC/Sectionizing/Ref2'
export BIGODM_DIR='/Users/pmh/data/sections/2014_i2b2_challenge_with_dai_normalized'
export MEDSPACY_DIR='/Users/pmh/data/sections/data/medspacy_out'

export CLASSIFIER_OUT="${RESULT_DIR}/classifiers"
export MERGED_OUT="${RESULT_DIR}/merged"

mkdir -p "${CLASSIFIER_OUT}"
mkdir -p "${MERGED_OUT}"

export METHOD=voting
export SYS_DIR=${RESULT_DIR}/${METHOD}
mkdir -p ${SYS_DIR}

mkdir -p ${RESULT_DIR}/etude

## Rules-based medspaCy sectionizer
${SECTIONIZER_CONDA}/bin/python3 \
    "${SECTIONIZER_DIR}/medspacy/medspaCy_sectionizer.py" \
    --types-dir /Users/pmh/git/ots-ensemble-systems/types \
    --input-dir "${TEXTRACTOR_DIR}/brat5" \
    --output-dir "${CLASSIFIER_OUT}/rules_brat5"

## SVM-based sectionizer using spaCy and scikit-learn
${SECTIONIZER_CONDA}/bin/python3 \
    "${SECTIONIZER_DIR}/svm-spacy/spaCY-SVM_sectionizer.py" \
    --types-dir /Users/pmh/git/ots-ensemble-systems/types \
    --input-dir "${TEXTRACTOR_DIR}/brat5"  \
    --output-dir "${CLASSIFIER_OUT}/svm_brat5_rbf" \
    --model-dir "${MEDSPACY_DIR}_svm_brat5_rbf" \
    --svm-kernel "rbf"

## Merge the oracle/reference annotation with the above classifiers to
## generate a single input corpus for the meta-classifier ensemble
## system to read in
${ENSEMBLE_CONDA}/bin/python3 \
    ${ENSEMBLE_DIR}/medspaCy/sectionizers-converter.py \
    --types-dir /Users/pmh/git/ots-ensemble-systems/types \
    --input-ref-dir "${TEXTRACTOR_DIR}/brat5" \
    --input-sharpn-systems "${CLASSIFIER_OUT}" \
    --output-dir "${MERGED_OUT}"

export CLASSIFIERS=12
export MINVOTES=1

## Simple voting ensemble system
${ENSEMBLE_CONDA}/bin/python3 \
    ${ENSEMBLE_DIR}/medspaCy/voting-ensemble.py \
    --types-dir /Users/pmh/git/ots-ensemble-systems/types \
    --file-list /tmp/sample.txt \
    --input-dir "${MERGED_OUT}" \
    --voting-unit sentence \
    --classifier-list ${CLASSIFIERS} \
    --min-vote ${MINVOTES} \
    --zero-strategy drop \
    --output-dir ${SYS_DIR}

export MATCH_FLAG=partial

${ETUDE_CONDA}/bin/python3 ${ETUDE_DIR}/etude.py \
    --reference-conf ${CONFIG_DIR}/brat/sections_textractor_brat.conf \
    --reference-input "${TEXTRACTOR_DIR}/brat5" \
    --test-conf ${CONFIG_DIR}/uima/sections_note-nlp_xmi.conf \
    --test-input ${SYS_DIR} \
    --score-key Parent \
    --score-value Header \
    --file-suffix ".ann" ".xmi" \
    --fuzzy-match-flags ${MATCH_FLAG} \
    --metrics Accuracy TP FP FN TN Recall Precision F1 \
    > ${RESULT_DIR}/etude/${METHOD}_${MINVOTES}_${CLASSIFIERS}.log

## TODO - update grepping of stats for easy summary csv
#export COVERAGE=`grep micro ${RESULT_DIR}/etude/${METHOD}_${MINVOTES}_${CLASSIFIERS}.log | cut -f 2 | head -n 1 | tr '\n' '\t'`
#export ACCURACY=`grep micro ${RESULT_DIR}/etude/${METHOD}_${MINVOTES}_${CLASSIFIERS}.log | cut -f 2 | tail -n 1 | tr '\n' '\t'`
    
#echo "${METHOD}	${CLASSIFIERS}	${ACCURACY}${COVERAGE}${MINVOTES}" \
#	 >> ${RESULT_FILE}
