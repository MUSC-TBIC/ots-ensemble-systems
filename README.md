
This repository contains Python and Java example implementations of a
range of post-hoc ensemble generation algorithms.  Algorithms for
post-hoc ensemble generation embody different approaches for taking
the output of disparate models and synthesizing (or fusing) their
individual contributions into a single, better output.

The Python examples are built around
[medspaCy](https://github.com/medspacy/medspacy/), itself an extension
of the [spaCy](https://spacy.io/) framework. Sample data is available
from the [n2c2 datasets](https://n2c2.dbmi.hms.harvard.edu/data-sets)
website.

# medspaCy Implementations #

## conda Set-Up ##

```

conda create -n ensemble-py3.8 python=3.8
conda activate ensemble-py3.8

pip install --upgrade pip

pip install -r requirements.txt

```

After installing all the required Python packages, basic unit testing
can be run from the `medspaCy` folder. The following command will
write the results and coverage of these tests to the folder
`medspaCy/cov_html3.8`:

```

python -m pytest --cov-report html:cov_html3.8 --cov=./ tests

```


## Data Set-Up ##

Three sample corpora are required to run the base Python demos. These
corpora must be locally downloaded due to individual data use
agreements (DUAs) required for each dataset. We have included a demo
showing how to run the algorithms for ensembling: span-matching
algorithms (e.g., for simple named entity recognition without
subtypes), normalization algorithms (e.g., for named entity
normalization), and contextual attribute algorithms (e.g., negation or
subject).

- [2008 i2b2 Obesity Challenge](https://n2c2.dbmi.hms.harvard.edu/2008-challenge)
- [2009 i2b2 Medication Challenge](https://n2c2.dbmi.hms.harvard.edu/2009-challenge)
- [2019 n2c2/UMass Track on Clinical Concept Normalization](https://n2c2.dbmi.hms.harvard.edu/2019-track-3)

Because the algorithms ensemble the output of multiple models into a
single output, you will also need to download sample output from the
top teams from the same sites listed above. Each corpus comes in its
own particular format.  Our code presupposes that the input corpus has
been formatted according to the [SHARP-n style annotation
schema](https://doi.org/10.1186/2041-1480-4-1). (Any corpus that has
been converted into this format should be compatible with the sample
code.)  To help with that conversion, we have included a series of
shell scripts in the root directory of this repository named
`prep-X.sh.TEMPLATE`. Copy these template files to the equivalent file
ending in `.sh`. At the start of each `.sh` script file is a set of
environment variables that need to localized to your machine's
paths. For instance, in `prep-spans.sh`, `ENSEMBLE_DIR` should be
pointed at the root of this repository and `I2B2_2009_DIR` should
point your local copy of the 2009 i2b2 Medications Challenge
dataset. The rough outline of expected folders and files is also
provided in the shell script.

*NB:* We use the `*.TEMPLATE` suffix for the base scripts so that any
changes we make to these scripts upstream in the repository won't
automatically wipe out any local customizations you may have
made. This does mean that you may need to manually update (or use a
diff/merge tool) your scripts from time to time.

The `prep-X.sh` scripts convert a corpus to the SHARP-n schema (e.g.,
`n2c2-2019-track3-converter.py`). Then, the script creates a best-case
scenario ensemble which looks at all the outputs provided by models
and the reference (e.g., `oracle-ensemble.py`).  If the right output
was recommend by any of the models, it chooses that output.
Otherwise, it chooses a known wrong answer.  This oracle system helps
determine a ceiling for the model outputs given the task at hand.
Finally, for each of the supported ensemble methods (currently, voting
and decision templates), the script runs the algorithm on each
individual input model on its own.  The performance from these runs
determines the baseline performance when ensemble size = 1 using
[ETUDE](https://github.com/musc-tbic/etude-engine), an evaluation tool
for unstructured data and extractions. 

## Growing and/or Pruning Ensembles

The latter half of the `prep-X.sh` scripts provide a pattern for how
to evaluate progressively larger and smaller ensembles of models. In
former case, this process is sometimes called "growing ensembles" or
"buidling ensembles".  In the latter case, this process is usually
called "pruning ensembles".

We have made this pattern framework explicit in the
`score-X-kernel.sh` scripts that parallel the `prep-X.sh` scripts.
Again, you will need to update the appropriate environment variables
at the top of the files. Further, the `score-X.sh` scripts show how to
progressively call the `score-X-kernel.sh` script for each epoch of
ensemble size as you grow (or shrink) is. In other words, you may find
it easier to run single instances of `score-spans-kernel.sh` or you
may want to run large batches of `score-spans-kernel.sh` by adding
multiple calls to `score-spans.sh` and running that script instead.

Finally, check the file pointed to by `$RESULT_FILE` for an
accumulated record of performance results across your experiments.

## SHARP-n Style Annotation Schema ##

In the long-term, you'll want to add your own models to the ensemble
to improve performance. These models should fairly easily fit into the
pipeline as long as they adhere to the SHARP-n schema.

(More details to come on how we mapped from the sample source corpora
to the SHARP-n schema.)

Mapping concept normalizations (2019 n2c2/UMass Track 3) from the original reference to SHARPn type system.

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



Mapping medication annotation spans from the original 2009 i2b2 reference to SHARPn type system.

"...previous allergic reaction to intravenous *contrast dye* that..."
  
```

<textsem:IdentifiedAnnotation xmi:id="23"
    discoveryTechnique="1"
    begin="680" end="692" sofa="1"/>

<omop_cdm:Note_Nlp_TableProperties xmi:id="313"
          offset="680"
          note_nlp_source_concept_id="..."
          nlp_system="Majority Voting Ensemble System"
          term_modifiers="confidence=0.25;weighted_confidence=0.25"
          begin="680" end="692" sofa="1"/>

```

Mapping context attributes for a concept from the original i2b2 2008 reference to SHARPn type system.

```

  <textsem:IdentifiedAnnotation
    xmi:id="9"
    ontologyConceptArray="Asthma"
    polarity="0"
    uncertainty="0"
    discoveryTechnique="0"
    begin="0" end="0" sofa="1"/>

  <textsem:IdentifiedAnnotation
    xmi:id="8"
    ontologyConceptArray="CAD"
    polarity="1"
    uncertainty="0"
    discoveryTechnique="0"
    begin="0" end="0" sofa="1"/>

  <textsem:IdentifiedAnnotation
    xmi:id="10"
    polarity="0"
    uncertainty="1"
    ontologyConceptArray="GERD"
    discoveryTechnique="0"
    begin="0" end="0" sofa="1"/>
    
```


# Apache UIMA Implementations (Java) #

(Forthcoming)

# Java Implementations #

## Voting-ensemble method framework

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


## voting

`vote.java`

## voting pruned

`voteSearch.java`

	to get a pruned set of deidentification models, run voteSearch.java
	then run vote.java with the pruned set
	
## decision template method

`javac -cp /path/to/jsoup/jsoup-1.14.3.jar DTM.java`

	for weighted DTM, set the 'ifWeight' parameter to true
	
## SVM based stack learning
	
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
	
## searn-based stack learning

### To create feature vector file

		1. AddPredictionsVW.java
		2. CRFToVWstack.java
		
### To train a model
		$trFile: training feature vector file
		$model: model file
	
```
		vw -k -c --passes 20 -b 32 --holdout_off -l 0.025 --noconstant --ngram 3 -d $trFile --search_task sequence --search 49 -f $model
```

### To predict:
		$tsFile: test feature vector file
		$model: model file
		$prFile: system prediction file
		
		vw -t -d $tsFile -i $model -p $prFile --ring_size 100000
			
### To output XML files to destination directory

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


## Code for semantic type match

	To create semantic mapping between two corpora: TypeMatch.java
	To convert the source directory with target semantic types: Cnv.java
