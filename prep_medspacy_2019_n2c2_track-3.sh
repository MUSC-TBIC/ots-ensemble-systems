#!/bin/zsh

export ENSEMBLE_DIR=/Users/pmh/git/ots-ensemble-systems/medspaCy
export ENSEMBLE_CONDA=~/opt/anaconda3/envs/ensemble-py3.8
export ETUDE_DIR=/Users/pmh/git/etude
export ETUDE_CONDA=~/opt/anaconda3/envs/etude-py3.7
export CONFIG_DIR=/Users/pmh/git/etude-engine-configs/uima

export RESULT_DIR=/Users/pmh/git/ots-ensemble-systems/data/out

export TASK=2019_n2c2_track3
mkdir -p ${RESULT_DIR}/${TASK}/etude

export RESULT_FILE=/Users/pmh/git/ots-ensemble-systems/data/out/${TASK}/${TASK}_results.csv

echo "Method	Classifiers	Accuracy	Coverage	MinVote" \
     > ${RESULT_FILE}

export INPUT_TEXT_DIR=~/data/n2c2/2019_n2c2_track-3/test/test_note
export INPUT_NORM_DIR=~/data/n2c2/2019_n2c2_track-3/test/test_norm
export INPUT_SYSTEMS_DIR=~/data/n2c2/2019_n2c2_track-3/top10_outputs
export INPUT_FILE_LIST=~/data/n2c2/2019_n2c2_track-3/test/test_file_list.txt
##export INPUT_FILE_LIST=~/data/n2c2/2019_n2c2_track-3/test/first_file.txt

export MERGED_DIR=${RESULT_DIR}/${TASK}/merged
mkdir -p ${MERGED_DIR}

python3 ${ENSEMBLE_DIR}/n2c2-2019-track3-converter.py \
  --input-text ${INPUT_TEXT_DIR} \
  --input-norm ${INPUT_NORM_DIR} \
  --input-systems ${INPUT_SYSTEMS_DIR} \
  --file-list ${INPUT_FILE_LIST} \
  --output-dir ${MERGED_DIR}

export REF_DIR=${RESULT_DIR}/${TASK}/ref
mkdir -p ${REF_DIR}
