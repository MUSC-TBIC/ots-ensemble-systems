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

export TASK=2019_n2c2_track3

export N2C2_2019_DIR=/Users/pmh/data/n2c2/2019_n2c2_track-3

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

export RESULT_DIR=${ENSEMBLE_DIR}/data/out
export RESULT_FILE=${RESULT_DIR}/${TASK}/${TASK}_results.csv

echo "Method	Classifiers	Accuracy	Coverage	MinVote" \
     > ${RESULT_FILE}

## RESULT_DIR/2019_n2c2_track3
## |-- 2019_n2c2_track3_results.csv
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

export REF_DIR=${RESULT_DIR}/${TASK}/ref
mkdir -p "${REF_DIR}"

mkdir -p ${RESULT_DIR}/${TASK}/etude

export METHOD=voting
export SYS_DIR=${RESULT_DIR}/${TASK}/${METHOD}
mkdir -p ${SYS_DIR}

## Merge the oracle/reference annotation with the above classifiers to
## generate a single input corpus for the meta-classifier ensemble
## system to read in
${ENSEMBLE_CONDA}/bin/python3 \
    ${ENSEMBLE_DIR}/medspaCy/n2c2-2019-track3-converter.py \
    --input-text ${N2C2_2019_DIR}/test/test_note \
    --input-norm ${N2C2_2019_DIR}/test/test_norm \
    --input-systems ${N2C2_2019_DIR}/top10_outputs \
    --file-list ${N2C2_2019_DIR}/test/test_file_list.txt \
    --output-dir ${MERGED_OUT}


## Create an oracle of best possible output
${ENSEMBLE_CONDA}/bin/python3 \
    ${ENSEMBLE_DIR}/medspaCy/oracle-ensemble.py \
    --types-dir ${ENSEMBLE_DIR}/types \
    --input-dir "${MERGED_OUT}" \
    --voting-unit span \
    --ref-dir ${REF_DIR}


export METHOD=voting
export MINVOTES=1
for CLASSIFIERS in {1..10}
do

    export SYS_DIR=${RESULT_DIR}/${TASK}/${METHOD}/${MINVOTES}_${CLASSIFIERS}
    mkdir -p ${SYS_DIR}
    
    ## Simple voting ensemble system
    ${ENSEMBLE_CONDA}/bin/python3 \
        ${ENSEMBLE_DIR}/medspaCy/voting-ensemble.py \
        --types-dir ${ENSEMBLE_DIR}/types \
        --input-dir "${MERGED_OUT}" \
        --voting-unit span \
        --classifier-list ${CLASSIFIERS} \
        --min-votes ${MINVOTES} \
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
      > ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${CLASSIFIERS}.log

    export COVERAGE=`grep micro ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${CLASSIFIERS}.log | cut -f 2 | head -n 1 | tr '\n' '\t'`
    export ACCURACY=`grep micro ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${CLASSIFIERS}.log | cut -f 2 | tail -n 1 | tr '\n' '\t'`
    
    echo "${METHOD}	${CLASSIFIERS}	${ACCURACY}${COVERAGE}${MINVOTES}" \
        >> ${RESULT_FILE}
done
