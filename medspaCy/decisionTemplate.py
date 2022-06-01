import argparse
import glob
import os
import re

import logging as log

from tqdm import tqdm

import spacy
import medspacy
import cassis

import pickle

from libTypeSystem import loadTypeSystem
from libTypeSystem import metadata_typeString, umlsConcept_typeString
from libTypeSystem import eventMention_typeString, modifier_typeString, timeMention_typeString

from libEnsemble import cosineSpannedVotes, cosineDocVotes

    
## Grab all the CUIs and their xmi:id's
def extractCuiMap( cas ):
    xmiId2cui = {}
    for umls_concept in cas.select( umlsConcept_typeString ):
        xmi_id = umls_concept.xmiID
        cui = umls_concept.cui
        xmiId2cui[ xmi_id ] = cui
    return( xmiId2cui )


def seedSpansInKb( cas ,
                   census ,
                   decision_profiles ,
                   kb ,
                   xmiId2cui ,
                   annotationTypeString ,
                   trainPhase ,
                   top_classifier_id ,
                   weighting ):
    ########
    for annot in cas.select( annotationTypeString ):
        technique = annot.discoveryTechnique
        if( ( trainPhase and technique != '0' ) or
            ( not trainPhase and technique != top_classifier_id ) ):
            continue
        begin_offset = annot.begin
        end_offset = annot.end
        span = '{}-{}'.format( begin_offset , end_offset )
        kb[ span ] = {}
        kb[ span ][ 'begin_offset' ] = begin_offset
        kb[ span ][ 'end_offset' ] = end_offset
        kb[ span ][ 'norm_counts' ] = {}
        kb[ span ][ 'norm_weights' ] = {}
        kb[ span ][ 'decision_profile' ] = {}
        try:
            ## ontologyConceptArray seems to always be an int
            concept_id = int( annot.ontologyConceptArray )
            cui = xmiId2cui[ concept_id ]
        except AttributeError as e:
            if( annotationTypeString.endswith( 'EventMention' ) ):
                ## ontologyConceptArr seems to always be a list
                if( type( [] ) == type( annot.ontologyConceptArr ) ):
                    ontology_concept = annot.ontologyConceptArr[ 0 ]
                    ## Because this concept is the rich representation, we
                    ## can just directly get the CUI.  It is equivalent to
                    ## using the follow two-step approach:
                    ## concept_id = ontology_concept.get( 'xmiID' )
                    ## cui = xmiId2cui[ concept_id ]
                    cui = ontology_concept.get( 'cui' )
                else:
                    ## Bailing because we can't figure out how to unpack
                    ## the CUIs
                    cui = 'span'
            elif( annotationTypeString.endswith( 'Modifier' ) ):
                cui = annot.category
                if( cui is None ):
                    cui = 'span'
        except TypeError as e:
            ## A TypeError here means occurs when
            ## ontologyConceptArray is not defined, meaning
            ## that there is no associated CUI
            cui = 'span'
        if( not trainPhase and weighting == 'ranked' ):
            weight = 1 / int( technique )
        else:
            weight = 1
        kb[ span ][ 'norm_counts' ][ cui ] = 1
        kb[ span ][ 'norm_weights' ][ cui ] = weight
        ## During training, track the global frequency of reference
        ## concepts
        if( trainPhase ):
            if( cui not in census ):
                census[ cui ] = 0
                decision_profiles[ cui ] = {}
            kb[ span ][ 'reference_type' ] = cui
        else:
            kb[ span ][ 'decision_profile' ][ technique ] = {}
            kb[ span ][ 'decision_profile' ][ technique ][ cui ] = weight
    return( census , decision_profiles , kb )


def processRemainingAnnotations( cas ,
                                 filename ,
                                 census ,
                                 decision_profiles ,
                                 kb ,
                                 xmiId2cui ,
                                 annotationTypeString ,
                                 trainPhase ,
                                 classifiers ,
                                 top_classifier_id ,
                                 votingUnit ,
                                 weighting ,
                                 partialMatchWeight ):
    ########
    for annot in cas.select( annotationTypeString ):
        technique = annot.discoveryTechnique
        if( technique == '0' or
            technique not in classifiers or
            ## We already took care of the top_classifier above
            ## for span-based voting during the testing phase
            ( not trainPhase and votingUnit == 'span' and technique == top_classifier_id ) ):
            continue
        ## TODO - refactor variable named 'cui' to reflect
        ##        more fluid use across annotation types
        if( votingUnit == 'sentence' ):
            cui = 'section'
        elif( votingUnit == 'span' ):
            try:
                concept_id = int( annot.ontologyConceptArray )
                cui = xmiId2cui[ concept_id ]
            except AttributeError as e:
                if( annotationTypeString.endswith( 'EventMention' ) ):
                    ## ontologyConceptArr seems to always be a list
                    if( type( [] ) == type( annot.ontologyConceptArr ) ):
                        ontology_concept = annot.ontologyConceptArr[ 0 ]
                        ## Because this concept is the rich representation, we
                        ## can just directly get the CUI.  It is equivalent to
                        ## using the follow two-step approach:
                        ## concept_id = ontology_concept.get( 'xmiID' )
                        ## cui = xmiId2cui[ concept_id ]
                        cui = ontology_concept.get( 'cui' )
                    else:
                        ## Bailing because we can't figure out how to unpack
                        ## the CUIs
                        cui = 'span'
                elif( annotationTypeString.endswith( 'Modifier' ) ):
                    cui = annot.category
                    if( cui is None ):
                        cui = 'span'
            except TypeError as e:
                ## A TypeError here means occurs when
                ## ontologyConceptArray is not defined, meaning
                ## that there is no associated CUI
                cui = 'span'
        elif( votingUnit == 'doc' ):
            ## TODO - refactor how we extract the concept name
            ##        when this is ported to use real CUIs
            concept = annot.ontologyConceptArray
        ################
        begin_offset = annot.begin
        end_offset = annot.end
        span = '{}-{}'.format( begin_offset , end_offset )
        if( weighting == 'ranked' ):
            weight = 1 / int( technique )
        else:
            weight = 1
        ######################################################
        if( votingUnit == 'doc' ):
            if( concept not in kb ):
                kb[ concept ] = {}
            ####
            attribute_values = {}
            if( 'polarity' in attribute_list ):
                attribute_values[ 'polarity' ] = annot.polarity
            else:
                attribute_values[ 'polarity' ] = '0'
            ####
            if( 'uncertainty' in attribute_list ):
                attribute_values[ 'uncertainty' ] = annot.uncertainty
            else:
                attribute_values[ 'uncertainty' ] = '0'
            ####
            for attribute in attribute_list:
                attrib_val = attribute_values[ attribute ]
                ##
                if( attribute not in kb[ concept ] ):
                    kb[ concept ][ attribute ] = {}
                    ## We treat underspecified attributes as zero
                    kb[ concept ][ attribute ][ 'reference_type' ] = '0'
                    kb[ concept ][ attribute ][ 'decision_profile' ] = {}
                kb[ concept ][ attribute ][ 'decision_profile' ][ technique ] = {}
                kb[ concept ][ attribute ][ 'decision_profile' ][ technique ][ attrib_val ] = weight
                ## During training, increment the global frequency of
                ## attributes and values
                if( trainPhase ):
                    if( attribute not in census ):
                        census[ attribute ] = {}
                    if( attrib_val not in census[ attribute ] ):
                        census[ attribute ][ attrib_val ] = 0
                    census[ attribute ][ attrib_val ] += 1
                    ref_attrib_val = kb[ concept ][ attribute ][ 'reference_type' ]
                    if( attribute in decision_profiles ):
                        if( ref_attrib_val not in decision_profiles[ attribute ] ):
                            ## Is this even possible?
                            decision_profiles[ attribute ][ ref_attrib_val ] = {}
                        ##
                        if( technique not in decision_profiles[ attribute ][ ref_attrib_val ] ):
                            decision_profiles[ attribute ][ ref_attrib_val ][ technique ] = {}
                        if( attrib_val not in decision_profiles[ attribute ][ ref_attrib_val ][ technique ] ):
                            decision_profiles[ attribute ][ ref_attrib_val ][ technique ][ attrib_val ] = 0
                        decision_profiles[ attribute ][ ref_attrib_val ][ technique ][ attrib_val ] += weight
                    else:
                        ## TODO - how do we resolve this?
                        1
        elif( span in kb ):
            if( cui not in kb[ span ][ 'norm_counts' ] ):
                kb[ span ][ 'norm_counts' ][ cui ] = 0
                kb[ span ][ 'norm_weights' ][ cui ] = 0
            kb[ span ][ 'norm_counts' ][ cui ] += 1
            kb[ span ][ 'norm_weights' ][ cui ] += weight
            kb[ span ][ 'decision_profile' ][ technique ] = {}
            kb[ span ][ 'decision_profile' ][ technique ][ cui ] = weight
            if( trainPhase ):
                if( cui not in census ):
                    census[ cui ] = 0
                census[ cui ] += 1
                ref_cui = kb[ span ][ 'reference_type' ]
                if( ref_cui in decision_profiles ):
                    if( technique not in decision_profiles[ ref_cui ] ):
                        decision_profiles[ ref_cui ][ technique ] = {}
                    if( cui not in decision_profiles[ ref_cui ][ technique ] ):
                        decision_profiles[ ref_cui ][ technique ][ cui ] = 0
                    decision_profiles[ ref_cui ][ technique ][ cui ] += weight
                else:
                    ## TODO - how do we resolve this?
                    1
        else:
            ## Try to find any matching spans already registered
            ## in the kb
            matched_flag = False
            for anchor_span in kb:
                if( end_offset < kb[ anchor_span ][ 'begin_offset' ] ):
                    ## span ends before the anchor span
                    continue
                if( begin_offset > kb[ anchor_span ][ 'end_offset' ] ):
                    ## span starts after the anchor span
                    continue
                ref_cui = kb[ anchor_span ][ 'reference_type' ]
                if( begin_offset >= kb[ anchor_span ][ 'begin_offset' ] and
                    end_offset <= kb[ anchor_span ][ 'end_offset' ] ):
                    ## span is inside the anchor span
                    weight = weight * partialMatchWeight
                    if( cui not in kb[ anchor_span ][ 'norm_counts' ] ):
                        kb[ anchor_span ][ 'norm_counts' ][ cui ] = 0
                        kb[ anchor_span ][ 'norm_weights' ][ cui ] = 0
                    kb[ anchor_span ][ 'norm_counts' ][ cui ] += 1
                    kb[ anchor_span ][ 'norm_weights' ][ cui ] += weight
                    kb[ anchor_span ][ 'decision_profile' ][ technique ] = {}
                    kb[ anchor_span ][ 'decision_profile' ][ technique ][ cui ] = weight
                    if( trainPhase ):
                        if( cui not in census ):
                            census[ cui ] = 0
                        census[ cui ] += 1
                        if( ref_cui in decision_profiles ):
                            if( technique not in decision_profiles[ ref_cui ] ):
                                decision_profiles[ ref_cui ][ technique ] = {}
                            if( cui not in decision_profiles[ ref_cui ][ technique ] ):
                                decision_profiles[ ref_cui ][ technique ][ cui ] = 0
                            decision_profiles[ ref_cui ][ technique ][ cui ] += weight
                        else:
                            ## TODO - how do we resolve this?
                            1
                    matched_flag = True
                    break
                if( begin_offset <= kb[ anchor_span ][ 'begin_offset' ] and
                    end_offset >= kb[ anchor_span ][ 'end_offset' ] ):
                    ## span fully contains the anchor span
                    ## .RRRR.
                    ## ..SS..
                    if( cui not in kb[ anchor_span ][ 'norm_counts' ] ):
                        kb[ anchor_span ][ 'norm_counts' ][ cui ] = 0
                        kb[ anchor_span ][ 'norm_weights' ][ cui ] = 0
                    kb[ anchor_span ][ 'norm_counts' ][ cui ] += 1
                    kb[ anchor_span ][ 'norm_weights' ][ cui ] += weight
                    kb[ anchor_span ][ 'decision_profile' ][ technique ] = {}
                    kb[ anchor_span ][ 'decision_profile' ][ technique ][ cui ] = weight
                    if( trainPhase ):
                        if( cui not in census ):
                            census[ cui ] = 0
                        census[ cui ] += 1
                        if( ref_cui in decision_profiles ):
                            if( technique not in decision_profiles[ ref_cui ] ):
                                decision_profiles[ ref_cui ][ technique ] = {}
                            if( cui not in decision_profiles[ ref_cui ][ technique ] ):
                                decision_profiles[ ref_cui ][ technique ][ cui ] = 0
                            decision_profiles[ ref_cui ][ technique ][ cui ] += weight
                        else:
                            ## TODO - how do we resolve this?
                            1
                    matched_flag = True
                elif( begin_offset >= kb[ anchor_span ][ 'begin_offset' ] and
                      begin_offset < kb[ anchor_span ][ 'end_offset' ] ):
                    ## span starts inside the anchor span
                    ## .RRR...
                    ## ..SSS..
                    weight = weight * partialMatchWeight
                    if( cui not in kb[ anchor_span ][ 'norm_counts' ] ):
                        kb[ anchor_span ][ 'norm_counts' ][ cui ] = 0
                        kb[ anchor_span ][ 'norm_weights' ][ cui ] = 0
                    kb[ anchor_span ][ 'norm_counts' ][ cui ] += 1
                    kb[ anchor_span ][ 'norm_weights' ][ cui ] += weight
                    kb[ anchor_span ][ 'decision_profile' ][ technique ] = {}
                    kb[ anchor_span ][ 'decision_profile' ][ technique ][ cui ] = weight
                    if( trainPhase ):
                        if( cui not in census ):
                            census[ cui ] = 0
                        census[ cui ] += 1
                        if( ref_cui in decision_profiles ):
                            if( technique not in decision_profiles[ ref_cui ] ):
                                decision_profiles[ ref_cui ][ technique ] = {}
                            if( cui not in decision_profiles[ ref_cui ][ technique ] ):
                                decision_profiles[ ref_cui ][ technique ][ cui ] = 0
                            decision_profiles[ ref_cui ][ technique ][ cui ] += weight
                        else:
                            ## TODO - how do we resolve this?
                            1
                    matched_flag = True
                elif( end_offset > kb[ anchor_span ][ 'begin_offset' ] and
                      end_offset <= kb[ anchor_span ][ 'end_offset' ] ):
                    ## span ends inside the anchor span
                    ## ...RRR.
                    ## ..SSS..
                    weight = weight * partialMatchWeight
                    if( cui not in kb[ anchor_span ][ 'norm_counts' ] ):
                        kb[ anchor_span ][ 'norm_counts' ][ cui ] = 0
                        kb[ anchor_span ][ 'norm_weights' ][ cui ] = 0
                    kb[ anchor_span ][ 'norm_counts' ][ cui ] += 1
                    kb[ anchor_span ][ 'norm_weights' ][ cui ] += weight
                    kb[ anchor_span ][ 'decision_profile' ][ technique ] = {}
                    kb[ anchor_span ][ 'decision_profile' ][ technique ][ cui ] = weight
                    if( trainPhase ):
                        if( cui not in census ):
                            census[ cui ] = 0
                        census[ cui ] += 1
                        if( ref_cui in decision_profiles ):
                            if( technique not in decision_profiles[ ref_cui ] ):
                                decision_profiles[ ref_cui ][ technique ] = {}
                            if( cui not in decision_profiles[ ref_cui ][ technique ] ):
                                decision_profiles[ ref_cui ][ technique ][ cui ] = 0
                            decision_profiles[ ref_cui ][ technique ][ cui ] += weight
                        else:
                            ## TODO - how do we resolve this?
                            1
                    matched_flag = True
                else:
                    ## How did we get here?
                    log.error( 'Somehow span {} and reference span {} are neither a match nor mismatch in file \'{}\''.format( span ,
                                                                                                                               anchor_span ,
                                                                                                                               filename ) )
            ####
            ## If we never matched another pre-existing span, then
            ## add a new anchor span to the kb
            if( not matched_flag and votingUnit == 'span' ):
                if( trainPhase ):
                    ## add to negative counts
                    census[ 'NONE' ] += 1
                    if( technique not in decision_profiles[ 'NONE' ] ):
                        decision_profiles[ 'NONE' ][ technique ] = {}
                    ## TODO - should this cui value be set to NONE as well?
                    if( cui not in decision_profiles[ 'NONE' ][ technique ] ):
                        decision_profiles[ 'NONE' ][ technique ][ cui ] = 0
                    decision_profiles[ 'NONE' ][ technique ][ cui ] += weight
                else:
                    kb[ span ] = {}
                    kb[ span ][ 'begin_offset' ] = begin_offset
                    kb[ span ][ 'end_offset' ] = end_offset
                    kb[ span ][ 'norm_counts' ] = {}
                    kb[ span ][ 'norm_weights' ] = {}
                    kb[ span ][ 'norm_counts' ][ cui ] = 1
                    kb[ span ][ 'norm_weights' ][ cui ] = weight
                    kb[ span ][ 'decision_profile' ] = {}
                    kb[ span ][ 'decision_profile' ][ technique ] = {}
                    kb[ span ][ 'decision_profile' ][ technique ][ cui ] = weight
    ########
    return( census , decision_profiles , kb )

    
def main( args , classifiers ):
    ############################
    trainPhase = False
    if( args.phase == 'train' ):
        trainPhase = True
    ############################
    typesystem , NoteNlp = loadTypeSystem( typesDir = args.typesDir ,
                                           typesFile = args.typesFile )
    annotation_types = []
    for type_string in [ 'textsem.IdentifiedAnnotation' ,
                         modifier_typeString ,
                         eventMention_typeString ]:
        try:
            typesystem.get_type( type_string )
        except:
            log.debug( 'Annotation type skipped because it is not present in the type system: {}'.format( type_string ) )
        else:
            annotation_types.append( type_string )
    ############################
    ## Seed the list of files to process either directly from the
    ## input directory or from the contents of --file-list
    filenames = []
    if( args.fileList is None ):
        filenames = sorted( [ os.path.basename( f ) for f in glob.glob( os.path.join( args.inputDir ,
                                                                                      '*.xmi' ) ) ] )
    else:
        with open( args.fileList , 'r' ) as fp:
            for line in fp:
                line = line.strip()
                filenames.append( line )
    ############################
    ## Read in the ranked order of classifiers
    ranked_classifiers = []
    if( args.rankFile is not None ):
        with open( args.rankFile , 'r' ) as fp:
            for line in fp:
                line = line.strip()
                cols = line.split( '\t' )
                ## If a header line exists, skip it
                if( cols[ 0 ] == 'Classifier' ):
                    continue
                ranked_classifiers.append( cols[ 0 ] )
    ############################
    ## TODO - programmatically determine the list of attributes to monitor
    attribute_list = [ 'polarity' , 'uncertainty' ]
    ####
    if( trainPhase ):
        census = {}
        decision_profiles = {}
        if( args.votingUnit == 'span' ):
            census[ 'NONE' ] = 0
            decision_profiles[ 'NONE' ] = {}
        elif( args.votingUnit == 'doc' ):
            for attribute in attribute_list:
                census[ attribute ] = {}
                census[ attribute ][ '0' ] = 0
                census[ attribute ][ 'NONE' ] = 0
                decision_profiles[ attribute ] = {}
                decision_profiles[ attribute ][ '0' ] = {}
                decision_profiles[ attribute ][ 'NONE' ] = {}
        elif( args.votingUnit == 'sentence' ):
            ## TODO - how is this different from spans?
            census[ 'NONE' ] = 0
            decision_profiles[ 'NONE' ] = {}
    else:
        census , decision_profiles = pickle.load( open( args.decisionProfilesPkl , 'rb' ) )
    trainModFlag = 0
    fileCount = 0
    ## Iterate over the files, covert to CAS, and write the XMI to disk
    for filename in tqdm( filenames ,
                          desc = 'Collecting Profiles (k={})'.format( len( classifiers ) ) ):
        ##
        classifier2id = {}
        id2classifier = {}
        xmiId2cui = {}
        ##
        if( args.fileList is None ):
            xmi_filename = filename
        else:
            xmi_filename = '{}.xmi'.format( filename )
        with open( os.path.join( args.inputDir , xmi_filename ) , 'rb' ) as fp:
            cas = cassis.load_cas_from_xmi( fp ,
                                            typesystem = typesystem )
        ## Grab the discoveryTechnique long names
        for metadata in cas.select( metadata_typeString ):
            classifier_name , classifier_id = metadata.other.split( '=' )
            if( classifier_id == '0' or
                classifier_id not in classifiers ):
                continue
            classifier2id[ classifier_name ] = classifier_id
            id2classifier[ classifier_id ] = classifier_name
        ## Grab all the CUIs and their xmi:id's
        xmiId2cui = extractCuiMap( cas )
        ## For sentence-based annotations, we want to seed the kb with
        ## all the spans of the sentences
        kb = {}
        if( args.votingUnit == 'sentence' ):
            for sentence in cas.select( 'org.apache.ctakes.typesystem.type.textspan.Sentence' ):
                begin_offset = sentence.begin
                end_offset = sentence.end
                span = '{}-{}'.format( begin_offset , end_offset )
                kb[ span ] = {}
                kb[ span ][ 'begin_offset' ] = begin_offset
                kb[ span ][ 'end_offset' ] = end_offset
                kb[ span ][ 'norm_counts' ] = {}
                kb[ span ][ 'norm_weights' ] = {}
                ## TODO - count both the number of times this sentence
                ##        is tagged as a section *and* how many times
                ##        it is tagged as a section with a particular
                ##        header type
                ## TODO - update when changing how CUI works for
                ## sections/sentences
                ## kb[ span ][ 'norm_counts' ][ <Section Type> ] = 0
                ## kb[ span ][ 'norm_weights' ][ <Section Type> ] = 0
                kb[ span ][ 'norm_counts' ][ 'section' ] = 0
                kb[ span ][ 'norm_weights' ][ 'section' ] = 0
        elif( args.votingUnit == 'span' ):
            ## For the span-based voting, we want to seed the kb with
            ## the spans of our reference system during training and our
            ## top ranked classifier during testing. If no rank file
            ## is given, then we'll just sort classifiers by their order
            ## provided at the command line.
            top_classifier_id = None
            provided_classifiers = None
            if( args.rankFile is None ):
                provided_classifiers = ', '.join( classifiers )
                for classifier_name in classifiers:
                    if( classifier_name  in id2classifier ):
                        top_classifier_id = classifier_name
                        break
            else:
                provided_classifiers = ', '.join( ranked_classifiers )
                for classifier_name in ranked_classifiers:
                    if( classifier_name in classifier2id ):
                        top_classifier_id = classifier2id[ classifier_name ]
                        break
            if( top_classifier_id is None ):
                ## TODO - provide option to not write a file if not classifiers available to vote
                log.warning( 'File \'{}\' does not contain any annotations matching the provided list of classifiers ({})'.format( filename ,
                                                                                                                                   provided_classifiers ) )
                continue
            trainModFlag += 1
            if( trainPhase ):
                if( args.autoSplit and trainModFlag % 10 in [ 0 , 1 , 2 , 3 , 4 , 5 , 6 ] ):
                    fileCount += 1
                elif( not args.autoSplit ):
                    fileCount += 1
                else:
                    continue
            else:
                if( args.autoSplit and trainModFlag % 10 in [ 7 , 8 , 9 ] ):
                    fileCount += 1
                elif( not args.autoSplit ):
                    fileCount += 1
                ## Run on all train and test files but write them to
                ## different folders so we get a score but still keep
                ## our workbench a little cleaner
                ##else:
                ##    1
            for annotationTypeString in annotation_types:
                census , decision_profiles , kb = seedSpansInKb( cas ,
                                                                 census ,
                                                                 decision_profiles ,
                                                                 kb ,
                                                                 xmiId2cui ,
                                                                 annotationTypeString ,
                                                                 trainPhase ,
                                                                 top_classifier_id ,
                                                                 args.weighting )
        elif( args.votingUnit == 'doc' ):
            ## For the doc-based voting, we want to seed the kb with
            ## the concept attribute types and values during training
            ## and our top ranked classifier during testing. If no
            ## rank file is given, then we'll just sort classifiers by
            ## their order provided at the command line.
            top_classifier_id = None
            provided_classifiers = None
            if( args.rankFile is None ):
                provided_classifiers = ', '.join( classifiers )
                for classifier_name in classifiers:
                    if( classifier_name  in id2classifier ):
                        top_classifier_id = classifier_name
                        break
            else:
                provided_classifiers = ', '.join( ranked_classifiers )
                for classifier_name in ranked_classifiers:
                    if( classifier_name in classifier2id ):
                        top_classifier_id = classifier2id[ classifier_name ]
                        break
            if( top_classifier_id is None ):
                ## TODO - provide option to not write a file if not classifiers available to vote
                log.warning( 'File \'{}\' does not contain any annotations matching the provided list of classifiers ({})'.format( filename ,
                                                                                                                                   provided_classifiers ) )
                continue
            trainModFlag += 1
            if( trainPhase ):
                if( args.autoSplit and trainModFlag % 10 in [ 0 , 1 , 2 , 3 , 4 , 5 , 6 ] ):
                    fileCount += 1
                elif( not args.autoSplit ):
                    fileCount += 1
                else:
                    continue
            else:
                if( args.autoSplit and trainModFlag % 10 in [ 7 , 8 , 9 ] ):
                    fileCount += 1
                elif( not args.autoSplit ):
                    fileCount += 1
                ## Run on all train and test files but write them to
                ## different folders so we get a score but still keep
                ## our workbench a little cleaner
                ##else:
                ##    1
            ####
            if( not trainPhase and args.weighting == 'ranked' ):
                weight = 1 / int( technique )
            else:
                weight = 1
            for annot in cas.select( 'textsem.IdentifiedAnnotation' ):
                technique = annot.discoveryTechnique
                if( ( trainPhase and technique != '0' ) or
                    ( not trainPhase and technique != top_classifier_id ) ):
                    continue
                ## TODO - refactor how we extract the concept name
                ##        when this is ported to use real CUIs
                concept = annot.ontologyConceptArray
                if( concept not in kb ):
                    kb[ concept ] = {}
                ####
                attribute_values = {}
                if( 'polarity' in attribute_list ):
                    attribute_values[ 'polarity' ] = annot.polarity
                else:
                    attribute_values[ 'polarity' ] = '0'
                ####
                if( 'uncertainty' in attribute_list ):
                    attribute_values[ 'uncertainty' ] = annot.uncertainty
                else:
                    attribute_values[ 'uncertainty' ] = '0'
                ####
                for attribute in attribute_list:
                    if( attribute not in kb[ concept ] ):
                        kb[ concept ][ attribute ] = {}
                        kb[ concept ][ attribute ][ 'decision_profile' ] = {}
                    ##
                    attrib_val = attribute_values[ attribute ]
                    ## During training, track the global frequency of
                    ## attributes and values
                    if( trainPhase ):
                        if( attribute not in census ):
                            census[ attribute ] = {}
                            decision_profiles[ attribute ] = {}
                        if( attrib_val not in census[ attribute ] ):
                            census[ attribute ][ attrib_val ] = 0
                        kb[ concept ][ attribute ][ 'reference_type' ] = attrib_val
                    else:
                        kb[ concept ][ attribute ][ 'decision_profile' ][ technique ] = {}
                        kb[ concept ][ attribute ][ 'decision_profile' ][ technique ][ attrib_val ] = weight
        ########
        ## Grab all the remaining annotations of interest and process them
        for annotationTypeString in annotation_types:
            census , decision_profiles , kb = processRemainingAnnotations( cas ,
                                                                           filename ,
                                                                           census ,
                                                                           decision_profiles ,
                                                                           kb ,
                                                                           xmiId2cui ,
                                                                           annotationTypeString ,
                                                                           trainPhase ,
                                                                           classifiers ,
                                                                           top_classifier_id ,
                                                                           args.votingUnit ,
                                                                           args.weighting ,
                                                                           args.partialMatchWeight )
        #########
        ## TODO - should I run this after aggregating decision profiles data structure
        ##        so we can generate outputs even for training on the same run? Maybe
        ##        save per-file kb to temporary disk to save on time?
        if( not trainPhase ):
            if( args.votingUnit == 'sentence' or
                args.votingUnit == 'span' ):
                cas = cosineSpannedVotes( cas ,
                                          NoteNlp ,
                                          kb ,
                                          decision_profiles ,
                                          classifiers ,
                                          args.votingUnit ,
                                          args.zeroStrategy )
            elif( args.votingUnit == 'doc' ):
                cas = cosineDocVotes( cas ,
                                      NoteNlp ,
                                      kb ,
                                      decision_profiles ,
                                      classifiers ,
                                      attribute_list ,
                                      args.zeroStrategy )
            ################
            if( args.outputDir is not None ):
                if( trainPhase and
                    ( not args.autoSplit or
                      trainModFlag % 10 in [ 0 , 1 , 2 , 3 , 4 , 5 , 6 ] ) ):
                    if( args.autoSplit ):
                        output_path = os.path.join( args.outputDir , 'train' , xmi_filename )
                    else:
                        output_path = os.path.join( args.outputDir , xmi_filename )
                else:
                    if( args.autoSplit ):
                        output_path = os.path.join( args.outputDir , 'test' , xmi_filename )
                    else:
                        output_path = os.path.join( args.outputDir , xmi_filename )
                ##
                cas.to_xmi( path = output_path ,
                            pretty_print = True )
    ####
    if( trainPhase ):
        log.info( 'Trained on {} files'.format( fileCount ) )
        ## Normalize the weights for a decision profile against
        ## the global frequency of a given annotation type
        if( args.votingUnit == 'sentence' or
            args.votingUnit == 'span' ):
            ## TODO - Are sentence decision profiles different?
            for ref_cui in decision_profiles:
                for technique in decision_profiles[ ref_cui ]:
                    for cui in decision_profiles[ ref_cui ][ technique ]:
                        technique_frequency = decision_profiles[ ref_cui ][ technique ][ cui ]
                        global_frequency = census[ ref_cui ]
                        if( global_frequency == 0 ):
                            ## TODO - verify all possible paths for this to be zero are valid
                            decision_profiles[ ref_cui ][ technique ][ cui ] = 0
                        else:
                            decision_profiles[ ref_cui ][ technique ][ cui ] = technique_frequency / global_frequency
        elif( args.votingUnit == 'doc' ):
            for attribute in decision_profiles:
                for ref_attrib_val in decision_profiles[ attribute ]:
                    for technique in decision_profiles[ attribute ][ ref_attrib_val ]:
                        for attrib_val in decision_profiles[ attribute ][ ref_attrib_val ][ technique ]:
                            technique_frequency = decision_profiles[ attribute ][ ref_attrib_val ][ technique ][ attrib_val ]
                            global_frequency = census[ attribute ][ attrib_val ]
                            decision_profiles[ attribute ][ ref_attrib_val ][ technique ][ attrib_val ] = technique_frequency / global_frequency
        ## Save the data structure for the test phase
        pickle.dump( [ census ,
                       decision_profiles ] ,
                     open( args.decisionProfilesPkl , 'wb' ) )
    else:
        log.info( 'Testing on {} files'.format( fileCount ) )


if __name__ == '__main__':
    parser = argparse.ArgumentParser( description = 'Simple voting ensemble system' )
    parser.add_argument( '-v' , '--verbose' ,
                         help = "Log at the DEBUG level" ,
                         action = "store_true" )
    parser.add_argument( '--phase' ,
                         required = True ,
                         choices = [ 'train' , 'test' ] ,
                         dest = 'phase' ,
                         help = 'Set the phase as either training or testing' )
    parser.add_argument( '--auto-split' , default = True ,
                         dest = 'autoSplit' ,
                         help = "Auto-split the directory into a 70/30 train/dev split (opposite of --no-split)" ,
                         action = "store_true" )
    parser.add_argument( '--no-split' , default = False ,
                         dest = 'autoSplit' ,
                         help = "Process all files without doing any further splits (opposite of --auto-split)" ,
                         action = "store_false" )
    parser.add_argument( '--partial-match-weight' ,
                         default = 1 ,
                         dest = 'partialMatchWeight' )
    parser.add_argument( '--types-dir' , default = None ,
                         dest = 'typesDir' ,
                         help = 'Directory containing the systems files need to be loaded' )
    parser.add_argument( '--types-file' , default = None ,
                         dest = 'typesFile' ,
                         help = 'File containing the base type system definition need to be loaded' )
    parser.add_argument( '--input-dir' ,
                         required = True ,
                         dest = 'inputDir' ,
                         help = 'Input directory containing CAS XMI files' )
    parser.add_argument( '--file-list' , default = None ,
                         dest = 'fileList' ,
                         help = 'File containing the basename of all files in order' )
    parser.add_argument( '--ref-dir' ,
                         default = None ,
                         dest = 'refDir' ,
                         help = 'Output directory for writing the reference CAS XMI files to' )
    parser.add_argument( '--classifier-list' , nargs = '+' ,
                         default = None ,
                         dest = 'classifierList' ,
                         help = 'List of classifiers (space separated and by numerical id) to include' )
    parser.add_argument( '--decision-profiles-file' ,
                         required = True ,
                         dest = 'decisionProfilesPkl' ,
                         help = 'File containing the decision profiles data structured (pickled)' )
    parser.add_argument( '--classifier-rank-file' , default = None ,
                         dest = 'rankFile' ,
                         help = 'File containing the classifiers ranked in the best to worst performance order (used to break ties)' )
    parser.add_argument( '--zero-strategy' ,
                         default = 'CUI-less' ,
                         choices = [ 'drop' , 'CUI-less' ] ,
                         dest = 'zeroStrategy' ,
                         help = 'When no normalizations surpasses the decision profile simularity threshold, use this strategy to select a normalization' )
    parser.add_argument( '--overlap-strategy' ,
                         default = 'rank' ,
                         ## TODO - support additional strategies
                         ##choices = [ 'rank' , 'flatten' , 'longest', 'shortest' ] ,
                         choices = [ 'rank' ] ,
                         dest = 'overlapStrategy' ,
                         help = 'Strategy for resolving conflicts of span overlap between annotations when using the span as the voting unit' )
    parser.add_argument( '--classifier-weight-strategy' ,
                         default = 'balanced' ,
                         ## TODO - support additional strategies
                         choices = [ 'balanced' , 'ranked' ] ,
                         dest = 'weighting' ,
                         help = 'Strategy for weighting the relative importance of each classifier (ranked = 1/rank)' )
    parser.add_argument( '--voting-unit' ,
                         default = 'span' ,
                         choices = [ 'span' , 'sentence' , 'doc' ] ,
                         dest = 'votingUnit' ,
                         help = 'The unit that accumulates votes: "span" means to treat annotations as their own unit, "sentence" means to converge on all spans matching a sentence, "doc" aggregates all annotations at the document level' )
    parser.add_argument( '--tie-breaker' ,
                         default = 'random' ,
                         choices = [ 'random' , 'ranked' , 'confidenceScore' ] ,
                         dest = 'tieBreaker' ,
                         help = 'When multiple normalizations receive the same number of votes, use this strategy to resolve ties' )
    parser.add_argument( '--rank-file' ,
                         default = None ,
                         dest = 'rankFile' ,
                         help = 'File containing the ranked list of classifiers to be used in tie-breakers (earlier classifiers are chosen over later classifiers' )
    parser.add_argument( '--output-dir' ,
                         default = None ,
                         dest = 'outputDir' ,
                         help = 'Output directory for writing the oracle consolidated CAS XMI files to' )
    args = parser.parse_args()
    ## Set up logging
    if args.verbose:
        log.basicConfig( format = "%(levelname)s: %(message)s" ,
                         level = log.DEBUG )
        log.info( "Verbose output." )
        log.debug( "{}".format( args ) )
    else:
        log.basicConfig( format="%(levelname)s: %(message)s" ,
                         level = log.INFO )
    ##
    args.partialMatchWeight = float( args.partialMatchWeight )
    ## In order to support quoted and unquoted classifier lists, we'll
    ## check if there is a single argument and it contains a space. If
    ## so, we can assume it is safe to explode the first arg and
    ## create a list from that:
    ##
    ## --classifier-list 1 2 3
    ##     vs.
    ## --classifier-list "1 2 3"
    if( args.classifierList is not None and
        len( args.classifierList ) == 1 and
        ' ' in args.classifierList[ 0 ] ):
        args.classifierList = args.classifierList[ 0 ].split()
    ####
    main( args , args.classifierList )
