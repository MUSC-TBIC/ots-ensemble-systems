
# medspaCy #

## conda Set-Up ##

```

conda create -n ensemble-py3.8 python=3.8
conda activate ensemble-py3.8

pip install --upgrade pip

pip install -r requirements.txt

```

## SHARP-n Style Annotation Schema ##

Right LE pain

```

<!-- identified annotation -->
<textsem:IdentifiedAnnotation xmi:id="545" sofa="1" 
    begin="56" end="69" id="0" 
    ontologyConceptArr="587" 
	discoveryTechnique="0" confidence="0.0" 
	event="569"
	typeID="0" 
	polarity="0" uncertainty="0" 
    conditional="false" generic="false" historyOf="0"
    />

```

```

<!-- ontologyConceptArr -->
<refsem:UmlsConcept xmi:id="587"
    cui="C0564823"
	score="0.0" 
	disambiguated="false"
    />

```

# Voting-ensemble method framework

dependency: [jsoup](https://github.com/jhy/jsoup/releases/tag/jsoup-1.6.2)

how to run:

```

java -Xmx1g -cp target:<jsoup dir>/jsoup-1.6.2.jar \
  Voting \
  <threshold> \
  <source xml dir> \
  <output dir> \
  <system<sub>1</sub> dir> \
  <system<sub>2</sub> dir> ...

```

jsoup dir: the directory containing jsoup-1.6.2.jar
threshold: voting threshold, e.g., 1, 2
source xml dir: the directory containing XML files with `<TEXT>` tags (i2b2 2014 deid corpus format)
output dir: an output directory for voting ensemble
system<sub>1</sub> dir ~ system<sub>n</sub> dir: the directories containing the predictions of individual deidenfication systems


# voting

`vote.java`

# voting pruned

`voteSearch.java`

	to get a pruned set of deidentification models, run voteSearch.java
	then run vote.java with the pruned set
	
# decision template method

`DTM.java`

	for weighted DTM, set the 'ifWeight' parameter to true
	
# SVM based stack learning
	
To create feature vector file: 
	
```
		$trTxtDir: directory containing text files
		$oTrFile: feature vector file
		$oTrLFile: label file containing concept span information
		$cFile: label index file for multi-class svm, use i2b2_2014_stack.txt 
		$catFile: mapping file for semantic type and sub-semantic type, use 'i2b2_2014_type.txt'
		$refTrDir: reference standard directory
		$trDir1 ~ $trDir4: input directories (system output directory for each corpus)
		$fvFile: feature set definition file, use stackF_deid.txt
		
		java -Xmx10g -cp jsoup-1.6.2.jar:./ StackDeidNE $trTxtDir $oTrFile $oTrLFile $cFile $catFile $refTrDir $trDir1 $trDir2 $trDir3 $trDir4			
		java -Xmx1g StackFeature $fvFile $oTrFile $oTrFile
```
	
	To train a model:
```
	
		$model: model file

		$libHome/train -s 2 -c 0.1 -w25 0.8 $oTrFile $modelFile
```
	
To predict:

```
		$oTsFile: test feature vector file
		$modelFile: model file
		$oTsPrFile: system prediction file

		$libHome/predict -b 1 $oTsFile $modelFile $oTsPrFile
```

To output XML files to destination directory:

```	
		java -Xmx1g StackPredProbDeidNE $oTsPrFile $oTsLFile $ansDir $refTsDir $year $cFile $catFile
		java -Xmx1g -cp jsoup-1.6.2.jar:./ RemOverlapDeid $ansDir $refTsDir $year

```	
	
# searn-based stack learning

## To create feature vector file

		1. AddPredictionsVW.java
		2. CRFToVWstack.java
		
## To train a model
		$trFile: training feature vector file
		$model: model file
	
```
		vw -k -c --passes 20 -b 32 --holdout_off -l 0.025 --noconstant --ngram 3 -d $trFile --search_task sequence --search 49 -f $model
```

## To predict:
		$tsFile: test feature vector file
		$model: model file
		$prFile: system prediction file
		
		vw -t -d $tsFile -i $model -p $prFile --ring_size 100000
			
## To output XML files to destination directory

		$prFile: prediction output file
		$ansDir: output directory
		$txtDir: reference standard directory
		$catFile: mapping file for semantic type and sub-semantic type, use 'i2b2_2014_type.txt'
		$year: if i2b2 2016, '2016'. Otherwise '2014'
	
		$LFile: mapping file between vw class labels and i2b2 tags, use 'bioDeid_i2b2_vw.txt'
		$oTsFile: file containing sentence and token information
		
		#to combine sentence and token information for each word and predicted tag 
		java -Xmx6g VWToPredProbNew $oTsFile $prFile $LFile
		#to output XML files to destination directory:
		java -Xmx1g PredictOutProbDeidNew 2 $prFile $ansDir f 0.0 $txtDir $catFile $year


# Code for semantic type match

	To create semantic mapping between two corpora: TypeMatch.java
	To convert the source directory with target semantic types: Cnv.java
