import argparse
import glob
import os
import re

import logging as log

from tqdm import tqdm

import spacy
import medspacy
import cassis


def tallySpannedVotes( cas ,
                       NoteNlp ,
                       kb ,
                       classifiers ,
                       votingUnit ,
                       minVotes ,
                       zeroStrategy ):
    for span in kb:
        max_cui = 'CUI-less'
        max_cui_count = 0
        ## TODO - allow option to choose CUI based on weighted score
        if( votingUnit == 'sentence' ):
            max_norm_weights = kb[ span ][ 'norm_weights' ][ 'section' ]
        for cui in kb[ span ][ 'norm_counts' ]:
            cui_count = kb[ span ][ 'norm_counts' ][ cui ]
            if( cui_count > max_cui_count and
                cui_count >= minVotes ):
                max_cui = cui
                max_cui_count = cui_count
                if( votingUnit == 'span' ):
                    max_norm_weights = kb[ span ][ 'norm_weights' ][ cui ]
        if( zeroStrategy == 'drop' and
            ( ( votingUnit == 'span' and max_cui_count == 0 ) or
              ( votingUnit == 'sentence' and max_norm_weights < minVotes ) ) ):
            continue
        ## TODO - add special flag to set whether we want to track CUIs or not
        modifiers = [ 'confidence={}'.format( max_cui_count / len( classifiers ) ) ,
                      'weighted_confidence={}'.format( max_norm_weights / len( classifiers ) ) ]
        if( votingUnit == 'sentence' ):
            note_nlp = NoteNlp( begin = kb[ span ][ 'begin_offset' ] ,
                                end = kb[ span ][ 'end_offset' ] ,
                                offset = kb[ span ][ 'begin_offset' ] ,
                                nlp_system = 'Majority Voting Ensemble System' ,
                                term_modifiers = ';'.join( modifiers ) )
        elif( votingUnit == 'span' ):
            note_nlp = NoteNlp( begin = kb[ span ][ 'begin_offset' ] ,
                                end = kb[ span ][ 'end_offset' ] ,
                                offset = kb[ span ][ 'begin_offset' ] ,
                                nlp_system = 'Majority Voting Ensemble System' ,
                                note_nlp_source_concept_id = max_cui ,
                                term_modifiers = ';'.join( modifiers ) )
        cas.add_annotation( note_nlp )
    return( cas )


def tallyDocVotes( cas ,
                   NoteNlp ,
                   kb ,
                   classifiers ,
                   attribute_list ,
                   minVotes ,
                   zeroStrategy ):
    for concept in kb:
        ## If a concept doesn't meet the minimum vote threshold, then
        ## we treate the concept as "not mentioned" (and don't include
        ## the annotation at all)
        concept_count = kb[ concept ][ 'norm_counts' ]
        concept_weight = kb[ concept ][ 'norm_weights' ]
        ## TODO - should "unmentioned" entries also be tallied here as
        ##        a counter-proposal to present?
        if( concept_count < minVotes ):
            continue
        ##
        max_attribute_vals = {}
        max_attribute_counts = {}
        for attribute in attribute_list:
            for attrib_val in kb[ concept ][ attribute ][ 'norm_counts' ]:
                val_count = kb[ concept ][ attribute ][ 'norm_counts' ][ attrib_val ]
                if( attribute not in max_attribute_counts ):
                    max_attribute_vals[ attribute ] = attrib_val
                    max_attribute_counts[ attribute ] = val_count
                elif( val_count > max_attribute_counts[ attribute ] ):
                    max_attribute_vals[ attribute ] = attrib_val
                    max_attribute_counts[ attribute ] = val_count
                elif( val_count == max_attribute_counts[ attribute ] ):
                    ## For ties, we want to treat the most extreme or noticable value
                    ## as the preferred value.  -1 > 1 > 0
                    if( ( int( max_attribute_vals[ attribute ] ) == 0 ) or
                        ( int( max_attribute_vals[ attribute ] ) == 1 and
                          attrib_val == -1 ) ):
                        max_attribute_vals[ attribute ] = attrib_val
                        max_attribute_counts[ attribute ] = val_count
        ## TODO - Current scoring can only support a single key/value
        ## pair in the term_modifiers attribute
        ##modifiers = [ 'confidence={}'.format( int( concept_count ) / len( classifiers ) ) ,
        ##              'weighted_confidence={}'.format( int( concept_weight ) / len( classifiers ) ) ]
        modifiers = []
        term_exists = True
        if( 'polarity' in attribute_list ):
            ##modifiers.append( 'polarity={}'.format( int( max_attribute_vals[ 'polarity' ] ) ) )
            if( int( max_attribute_vals[ 'polarity' ] ) == -1 ):
                term_exists = False
        if( 'uncertainty' in attribute_list ):
            modifiers.append( 'uncertainty={}'.format( int( max_attribute_vals[ 'uncertainty' ] ) ) )
        else:
            modifiers.append( 'uncertainty={}'.format( 0 ) )
        note_nlp = NoteNlp( begin = 0 ,
                            end = 0 ,
                            offset = 0 ,
                            nlp_system = 'Majority Voting Ensemble System' ,
                            ## TODO - map this correctly to a CUI
                            note_nlp_source_concept_id = concept ,
                            term_exists = term_exists ,
                            term_modifiers = ';'.join( modifiers ) )
        cas.add_annotation( note_nlp )
    return( cas )


def main( args , classifiers ):
    ############################
    typesystem , NoteNlp = loadTypeSystem( args.typesDir )
    ############################
    ## Seed the list of files to process either directly from the
    ## input directory or from the contents of --file-list
    filenames = []
    if( args.fileList is None ):
        filenames = [ os.path.basename( f ) for f in glob.glob( os.path.join( args.inputDir ,
                                                                              '*.xmi' ) ) ]
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
    ## Iterate over the files, covert to CAS, and write the XMI to disk
    for filename in tqdm( filenames ,
                          desc = 'Voting (k={})'.format( len( classifiers ) ) ):
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
        for metadata in cas.select( 'refsem.Metadata' ):
            classifier_name , classifier_id = metadata.other.split( '=' )
            if( classifier_id == '0' or
                classifier_id not in classifiers ):
                continue
            classifier2id[ classifier_name ] = classifier_id
            id2classifier[ classifier_id ] = classifier_name
        ## Grab all the CUIs and their xmi:id's
        for umls_concept in cas.select( 'refsem.UmlsConcept' ):
            xmi_id = umls_concept.xmiID
            cui = umls_concept.cui
            xmiId2cui[ xmi_id ] = cui
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
            ## For the span-based voting, we want to see the kb with
            ## the spans of our top ranked classifier. If no rank file
            ## is given, then we'll just pick the first one provided
            ## at the command line
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
            for annot in cas.select( 'textsem.IdentifiedAnnotation' ):
                technique = annot.discoveryTechnique
                if( technique != top_classifier_id ):
                    continue
                begin_offset = annot.begin
                end_offset = annot.end
                span = '{}-{}'.format( begin_offset , end_offset )
                kb[ span ] = {}
                kb[ span ][ 'begin_offset' ] = begin_offset
                kb[ span ][ 'end_offset' ] = end_offset
                kb[ span ][ 'norm_counts' ] = {}
                kb[ span ][ 'norm_weights' ] = {}
                try:
                    concept_id = int( annot.ontologyConceptArray )
                    cui = xmiId2cui[ concept_id ]
                except TypeError as e:
                    ## A TypeError here means occurs when
                    ## ontologyConceptArray is not defined, meaning
                    ## that there is no associated CUI
                    cui = 'span'
                weight = 1
                kb[ span ][ 'norm_counts' ][ cui ] = 1
                kb[ span ][ 'norm_weights' ][ cui ] = weight
        elif( args.votingUnit == 'doc' ):
            for annot in cas.select( 'textsem.IdentifiedAnnotation' ):
                ## TODO - refactor how we extract the concept name
                ##        when this is ported to use real CUIs
                concept = annot.ontologyConceptArray
                if( concept in kb ):
                    continue
                kb[ concept ] = {}
                kb[ concept ][ 'norm_counts' ] = 0
                kb[ concept ][ 'norm_weights' ] = 0
                for attribute in attribute_list:
                    kb[ concept ][ attribute ] = {}
                    kb[ concept ][ attribute ][ 'norm_counts' ] = {}
                    kb[ concept ][ attribute ][ 'norm_weights' ] = {}
        ## Grab all...
        for annot in cas.select( 'textsem.IdentifiedAnnotation' ):
            technique = annot.discoveryTechnique
            if( technique == '0' or
                technique not in classifiers or
                ## We already took care of the top_classifier above
                ## for span-based voting
                ( args.votingUnit == 'span' and technique == top_classifier_id ) ):
                continue
            ## TODO - refactor variable named 'cui' to reflect
            ##        more fluid use across annotation types
            if( args.votingUnit == 'sentence' ):
                cui = 'section'
            elif( args.votingUnit == 'span' ):
                try:
                    concept_id = int( annot.ontologyConceptArray )
                    cui = xmiId2cui[ concept_id ]
                except TypeError as e:
                    ## A TypeError here means occurs when
                    ## ontologyConceptArray is not defined, meaning
                    ## that there is no associated CUI
                    cui = 'span'
            elif( args.votingUnit == 'doc' ):
                ## TODO - refactor how we extract the concept name
                ##        when this is ported to use real CUIs
                concept = annot.ontologyConceptArray
            ################
            begin_offset = annot.begin
            end_offset = annot.end
            span = '{}-{}'.format( begin_offset , end_offset )
            ######################################################
            if( args.votingUnit == 'doc' ):
                attribute_values = {}
                ####
                if( 'polarity' in attribute_list ):
                    attribute_values[ 'polarity' ] = annot.polarity
                else:
                    attribute_values[ 'polarity' ] = 0
                ####
                if( 'uncertainty' in attribute_list ):
                    attribute_values[ 'uncertainty' ] = annot.uncertainty
                else:
                    attribute_values[ 'uncertainty' ] = 0
                ####
                weight = 1
                kb[ concept ][ 'norm_counts' ] += 1
                kb[ concept ][ 'norm_weights' ] += weight
                for attribute in attribute_list:
                    attrib_val = attribute_values[ attribute ]
                    if( attrib_val not in kb[ concept ][ attribute ][ 'norm_counts' ] ):
                        kb[ concept ][ attribute ][ 'norm_counts' ][ attrib_val ] = 0
                        kb[ concept ][ attribute ][ 'norm_weights' ][ attrib_val ] = 0
                    kb[ concept ][ attribute ][ 'norm_counts' ][ attrib_val ] += 1
                    kb[ concept ][ attribute ][ 'norm_weights' ][ attrib_val ] += weight
            elif( span in kb ):
                weight = 1
                if( cui not in kb[ span ][ 'norm_counts' ] ):
                    kb[ span ][ 'norm_counts' ][ cui ] = 0
                    kb[ span ][ 'norm_weights' ][ cui ] = 0
                kb[ span ][ 'norm_counts' ][ cui ] += 1
                kb[ span ][ 'norm_weights' ][ cui ] += weight
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
                    if( begin_offset >= kb[ anchor_span ][ 'begin_offset' ] and
                        end_offset <= kb[ anchor_span ][ 'end_offset' ] ):
                        ## span is inside the anchor span
                        weight = 0.5
                        if( cui not in kb[ anchor_span ][ 'norm_counts' ] ):
                            kb[ anchor_span ][ 'norm_counts' ][ cui ] = 0
                            kb[ anchor_span ][ 'norm_weights' ][ cui ] = 0
                        kb[ anchor_span ][ 'norm_counts' ][ cui ] += 1
                        kb[ anchor_span ][ 'norm_weights' ][ cui ] += weight
                        matched_flag = True
                        break
                    if( begin_offset <= kb[ anchor_span ][ 'begin_offset' ] and
                        end_offset >= kb[ anchor_span ][ 'end_offset' ] ):
                        ## span fully contains the anchor span
                        ## .RRRR.
                        ## ..SS..
                        weight = 1
                        if( cui not in kb[ anchor_span ][ 'norm_counts' ] ):
                            kb[ anchor_span ][ 'norm_counts' ][ cui ] = 0
                            kb[ anchor_span ][ 'norm_weights' ][ cui ] = 0
                        kb[ anchor_span ][ 'norm_counts' ][ cui ] += 1
                        kb[ anchor_span ][ 'norm_weights' ][ cui ] += weight
                        matched_flag = True
                    elif( begin_offset >= kb[ anchor_span ][ 'begin_offset' ] and
                          begin_offset < kb[ anchor_span ][ 'end_offset' ] ):
                        ## span starts inside the anchor span
                        ## .RRR...
                        ## ..SSS..
                        weight = 0.5
                        if( cui not in kb[ anchor_span ][ 'norm_counts' ] ):
                            kb[ anchor_span ][ 'norm_counts' ][ cui ] = 0
                            kb[ anchor_span ][ 'norm_weights' ][ cui ] = 0
                        kb[ anchor_span ][ 'norm_counts' ][ cui ] += 1
                        kb[ anchor_span ][ 'norm_weights' ][ cui ] += weight
                        matched_flag = True
                    elif( end_offset > kb[ anchor_span ][ 'begin_offset' ] and
                          end_offset <= kb[ anchor_span ][ 'end_offset' ] ):
                        ## span ends inside the anchor span
                        ## ...RRR.
                        ## ..SSS..
                        weight = 0.5
                        if( cui not in kb[ anchor_span ][ 'norm_counts' ] ):
                            kb[ anchor_span ][ 'norm_counts' ][ cui ] = 0
                            kb[ anchor_span ][ 'norm_weights' ][ cui ] = 0
                        kb[ anchor_span ][ 'norm_counts' ][ cui ] += 1
                        kb[ anchor_span ][ 'norm_weights' ][ cui ] += weight
                        matched_flag = True
                    else:
                        ## How did we get here?
                        log.error( 'Somehow span {} and reference span {} are neither a match nor mismatch in file \'{}\''.format( span ,
                                                                                                                                   anchor_span ,
                                                                                                                                   filename ) )
                ####
                ## If we never matched another pre-existing span, then
                ## add a new anchor span to the kb
                if( not matched_flag and args.votingUnit == 'span' ):
                    weight = 1
                    kb[ span ] = {}
                    kb[ span ][ 'begin_offset' ] = begin_offset
                    kb[ span ][ 'end_offset' ] = end_offset
                    kb[ span ][ 'norm_counts' ] = {}
                    kb[ span ][ 'norm_weights' ] = {}
                    kb[ span ][ 'norm_counts' ][ cui ] = 1
                    kb[ span ][ 'norm_weights' ][ cui ] = weight
        #########
        if( args.votingUnit == 'sentence' or
            args.votingUnit == 'span' ):
            cas = tallySpannedVotes( cas ,
                                     NoteNlp ,
                                     kb ,
                                     classifiers ,
                                     args.votingUnit ,
                                     args.minVotes ,
                                     args.zeroStrategy )
        elif( args.votingUnit == 'doc' ):
            cas = tallyDocVotes( cas ,
                                 NoteNlp ,
                                 kb ,
                                 classifiers ,
                                 attribute_list ,
                                 args.minVotes ,
                                 args.zeroStrategy )
        ################
        if( args.outputDir is not None ):
            cas.to_xmi( path = os.path.join( args.outputDir , xmi_filename ) ,
                        pretty_print = True )

