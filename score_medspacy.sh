#!/bin/zsh

export ENSEMBLE_DIR=/Users/pmh/git/ots-ensemble-systems/medspaCy
export ENSEMBLE_CONDA=~/opt/anaconda3/envs/ensemble-py3.8
export ETUDE_DIR=/Users/pmh/git/etude
export ETUDE_CONDA=~/opt/anaconda3/envs/etude-py3.7
export CONFIG_DIR=/Users/pmh/git/etude-engine-configs/uima

export RESULT_DIR=/Users/pmh/git/ots-ensemble-systems/data/out

export TASK=2019_n2c2_track3

export RESULT_FILE=/Users/pmh/git/ots-ensemble-systems/data/out/${TASK}/${TASK}_results.csv

export INPUT_TEXT_DIR=~/data/n2c2/2019_n2c2_track-3/test/test_note
export INPUT_NORM_DIR=~/data/n2c2/2019_n2c2_track-3/test/test_norm
export INPUT_SYSTEMS_DIR=~/data/n2c2/2019_n2c2_track-3/top10_outputs
export INPUT_FILE_LIST=~/data/n2c2/2019_n2c2_track-3/test/test_file_list.txt
##export INPUT_FILE_LIST=~/data/n2c2/2019_n2c2_track-3/test/first_file.txt

export MERGED_DIR=${RESULT_DIR}/${TASK}/merged
export REF_DIR=${RESULT_DIR}/${TASK}/ref

if [[ -z $TEAMS ]]; then
    export TEAMS=1234567890
fi

if [[ -z $MAXVOTES ]]; then
    export MAXVOTES=10
fi

export MINVOTES=1

export METHOD=oracle
export SYS_DIR=${RESULT_DIR}/${TASK}/${METHOD}/${TEAMS}
mkdir -p ${SYS_DIR}

## TODO - we only need to run the ref-dir creation once so figure
##        out an elegant way to have it trigger only the first time
##          --ref-dir ${REF_DIR} \
python3 ${ENSEMBLE_DIR}/oracle-ensemble.py \
  --input-dir ${MERGED_DIR} \
  --classifier-list ${TEAMS} \
  --output-dir ${SYS_DIR} \
  --file-list ${INPUT_FILE_LIST}

${ETUDE_CONDA}/bin/python3 ${ETUDE_DIR}/etude.py \
  --reference-conf ${CONFIG_DIR}/ensemble_note-nlp_xmi.conf \
  --reference-input ${REF_DIR} \
  --test-conf ${CONFIG_DIR}/ensemble_note-nlp_xmi.conf \
  --test-input ${SYS_DIR} \
  --file-suffix ".xmi" \
  --fuzzy-match-flags exact \
  --score-normalization note_nlp_source_concept_id \
  --metrics Accuracy TP FP FN TN \
  > ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${TEAMS}.log

export COVERAGE=`grep micro ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${TEAMS}.log | cut -f 2 | head -n 1 | tr '\n' '\t'`
export ACCURACY=`grep micro ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${TEAMS}.log | cut -f 2 | tail -n 1 | tr '\n' '\t'`

echo "${METHOD}	${TEAMS}	${ACCURACY}${COVERAGE}${MINVOTES}" \
     >> ${RESULT_FILE}

export METHOD=voting
for MINVOTES in {1..${MAXVOTES}}
do
    export SYS_DIR=${RESULT_DIR}/${TASK}/${METHOD}/${MINVOTES}_${TEAMS}
    mkdir -p ${SYS_DIR}
    
    python3 ${ENSEMBLE_DIR}/voting-ensemble.py \
      --input-dir ${MERGED_DIR} \
      --classifier-list ${TEAMS} \
      --min-votes ${MINVOTES} \
      --zero-strategy drop \
      --output-dir ${SYS_DIR} \
      --file-list ${INPUT_FILE_LIST}

    ${ETUDE_CONDA}/bin/python3 ${ETUDE_DIR}/etude.py \
      --reference-conf ${CONFIG_DIR}/ensemble_note-nlp_xmi.conf \
      --reference-input ${REF_DIR} \
      --test-conf ${CONFIG_DIR}/ensemble_note-nlp_xmi.conf \
      --test-input ${SYS_DIR} \
      --file-suffix ".xmi" \
      --fuzzy-match-flags exact \
      --score-normalization note_nlp_source_concept_id \
      --metrics Accuracy TP FP FN TN \
      > ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${TEAMS}.log
    
    export COVERAGE=`grep micro ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${TEAMS}.log | cut -f 2 | head -n 1 | tr '\n' '\t'`
    export ACCURACY=`grep micro ${RESULT_DIR}/${TASK}/etude/${METHOD}_${MINVOTES}_${TEAMS}.log | cut -f 2 | tail -n 1 | tr '\n' '\t'`
    
    echo "${METHOD}	${TEAMS}	${ACCURACY}${COVERAGE}${MINVOTES}" \
	 >> ${RESULT_FILE}
done
