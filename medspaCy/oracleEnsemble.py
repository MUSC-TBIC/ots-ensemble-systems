import argparse
import glob
import os
import re

import logging as log

from tqdm import tqdm

import spacy
import medspacy
import cassis

from libTypeSystem import loadTypeSystem
from libTypeSystem import umlsConcept_typeString
from libEnsemble import tallySpannedVotes, tallyDocVotes


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
    ## TODO - programmatically determine the list of attributes to monitor
    attribute_list = [ 'polarity' , 'uncertainty' ]
    ############################
    ## Iterate over the files, covert to CAS, and write the XMI to disk
    for filename in tqdm( filenames ,
                          desc = 'Oracle' ):
        ##
        classifier2id = {}
        id2classifier = {}
        xmiId2cui = {}
        ####
        if( args.fileList is None ):
            xmi_filename = filename
        else:
            xmi_filename = '{}.xmi'.format( filename )
        with open( os.path.join( args.inputDir , xmi_filename ) , 'rb' ) as fp:
            ref_cas = cassis.load_cas_from_xmi( fp ,
                                                typesystem = typesystem )
        with open( os.path.join( args.inputDir , xmi_filename ) , 'rb' ) as fp:
            cas = cassis.load_cas_from_xmi( fp ,
                                            typesystem = typesystem )
        ## Grab all the CUIs and their xmi:id's
        for umls_concept in cas.select( umlsConcept_typeString ):
            xmi_id = umls_concept.xmiID
            cui = umls_concept.cui
            xmiId2cui[ xmi_id ] = cui
        ## Grab all...
        kb = {}
        oracle_kb = {}
        if( args.votingUnit == 'sentence' ):
            ## TODO - sentence level not supported yet
            pass
        elif( args.votingUnit == 'span' ):
            for annot in cas.select( 'textsem.IdentifiedAnnotation' ):
                technique = annot.discoveryTechnique
                if( technique != '0' ):
                    continue
                try:
                    concept_id = int( annot.ontologyConceptArray )
                    cui = xmiId2cui[ concept_id ]
                except TypeError as e:
                    ## A TypeError here means occurs when
                    ## ontologyConceptArray is not defined, meaning
                    ## that there is no associated CUI
                    cui = 'span'
                begin_offset = annot.begin
                end_offset = annot.end
                span = '{}-{}'.format( begin_offset , end_offset )
                oracle_kb[ span ] = {}
                oracle_kb[ span ][ 'begin_offset' ] = begin_offset
                oracle_kb[ span ][ 'end_offset' ] = end_offset
                oracle_kb[ span ][ 'norm_counts' ] = {}
                oracle_kb[ span ][ 'norm_weights' ] = {}
                oracle_kb[ span ][ 'norm_counts' ][ cui ] = 1
                oracle_kb[ span ][ 'norm_weights' ][ cui ] = 1
                if( cui == 'span' ):
                    note_nlp = NoteNlp( begin = begin_offset ,
                                        end = end_offset ,
                                        offset = begin_offset ,
                                        nlp_system = 'Reference Standard' )
                else:                        
                    note_nlp = NoteNlp( begin = begin_offset ,
                                        end = end_offset ,
                                        offset = begin_offset ,
                                        nlp_system = 'Reference Standard' ,
                                        note_nlp_source_concept_id = cui )
                ref_cas.add_annotation( note_nlp )
            ## Now that we've normalized our reference standard, we
            ## can check the classifiers to see if any of them match
            for annot in cas.select( 'textsem.IdentifiedAnnotation' ):
                technique = annot.discoveryTechnique
                if( technique == 0 or
                    classifiers is None or
                    technique not in classifiers ):
                    continue
                try:
                    concept_id = int( annot.ontologyConceptArray )
                    cui = xmiId2cui[ concept_id ]
                except TypeError as e:
                    ## A TypeError here means occurs when
                    ## ontologyConceptArray is not defined, meaning
                    ## that there is no associated CUI
                    cui = 'span'
                begin_offset = annot.begin
                end_offset = annot.end
                span = '{}-{}'.format( begin_offset , end_offset )
                ## TODO - we only support exact match oracle merging
                if( span in oracle_kb and
                    cui in oracle_kb[ span ][ 'norm_counts' ] ):
                    weight = 1
                    if( span not in kb ):
                        kb[ span ] = {}
                        kb[ span ][ 'begin_offset' ] = begin_offset
                        kb[ span ][ 'end_offset' ] = end_offset
                        kb[ span ][ 'norm_counts' ] = {}
                        kb[ span ][ 'norm_weights' ] = {}
                    if( cui not in kb[ span ][ 'norm_counts' ] ):
                        kb[ span ][ 'norm_counts' ][ cui ] = 0
                        kb[ span ][ 'norm_weights' ][ cui ] = 0
                    kb[ span ][ 'norm_counts' ][ cui ] += 1
                    kb[ span ][ 'norm_weights' ][ cui ] += weight
            ####
        elif( args.votingUnit == 'doc' ):
            for annot in cas.select( 'textsem.IdentifiedAnnotation' ):
                technique = annot.discoveryTechnique
                if( technique != '0' ):
                    continue
                ## TODO - refactor how we extract the concept name
                ##        when this is ported to use real CUIs
                concept = annot.ontologyConceptArray
                begin_offset = annot.begin
                end_offset = annot.end
                span = '{}-{}'.format( begin_offset , end_offset )
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
                ########
                oracle_kb[ concept ] = {}
                oracle_kb[ concept ][ 'begin_offset' ] = 0
                oracle_kb[ concept ][ 'end_offset' ] = 0
                oracle_kb[ concept ][ 'norm_counts' ] = 1
                oracle_kb[ concept ][ 'norm_weights' ] = weight
                for attribute in attribute_list:
                    oracle_kb[ concept ][ attribute ] = {}
                    oracle_kb[ concept ][ attribute ][ 'norm_counts' ] = {}
                    oracle_kb[ concept ][ attribute ][ 'norm_weights' ] = {}
                    if( attribute in attribute_values ):
                        attrib_val = attribute_values[ attribute ]
                    else:
                        attrib_val = 0
                    oracle_kb[ concept ][ attribute ][ 'norm_counts' ][ attrib_val ] = 1
                    oracle_kb[ concept ][ attribute ][ 'norm_weights' ][ attrib_val ] = weight
                #### Add this reference annotation to the reference file
                modifiers = []
                term_exists = True
                ## TODO - Current scoring can only support a single
                ## key/value pair in the term_modifiers attribute
                if( 'polarity' in attribute_list ):
                    ##modifiers.append( 'polarity={}'.format( int( attribute_values[ 'polarity' ] ) ) )
                    if( int( attribute_values[ 'polarity' ] ) == -1 ):
                        term_exists = False
                if( 'uncertainty' in attribute_list ):
                    modifiers.append( 'uncertainty={}'.format( int( attribute_values[ 'uncertainty' ] ) ) )
                else:
                    modifiers.append( 'uncertainty={}'.format( 0 ) )
                note_nlp = NoteNlp( begin = 0 ,
                                    end = 0 ,
                                    offset = 0 ,
                                    nlp_system = 'Reference Standard' ,
                                    ## TODO - map this correctly to a CUI
                                    note_nlp_source_concept_id = concept ,
                                    term_exists = term_exists ,
                                    term_modifiers = ';'.join( modifiers ) )
                ref_cas.add_annotation( note_nlp )
            ## Now that we've normalized our reference standard, we
            ## can check the classifiers to see if any of them match
            for annot in cas.select( 'textsem.IdentifiedAnnotation' ):
                technique = annot.discoveryTechnique
                if( technique == '0' or
                    classifiers is None or
                    technique not in classifiers ):
                    continue
                ## TODO - refactor how we extract the concept name
                ##        when this is ported to use real CUIs
                concept = annot.ontologyConceptArray
                if( concept not in oracle_kb ):
                    ## Skip this entry if it's not mentioned in the oracle
                    ## TODO - should we require that at least 1
                    ## classifier not list an annotation for it to
                    ## not be listed in the oracle output?
                    continue
                begin_offset = annot.begin
                end_offset = annot.end
                span = '{}-{}'.format( begin_offset , end_offset )
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
                ########
                if( concept not in oracle_kb ):
                    continue
                ####
                if( concept not in kb ):
                    kb[ concept ] = {}
                    kb[ concept ][ 'begin_offset' ] = 0
                    kb[ concept ][ 'end_offset' ] = 0
                    kb[ concept ][ 'norm_counts' ] = 0
                    kb[ concept ][ 'norm_weights' ] = 0
                ####
                for attribute in attribute_list:
                    if( attribute not in oracle_kb[ concept ] ):
                        continue
                    if( attribute in attribute_values ):
                        attrib_val = attribute_values[ attribute ]
                    else:
                        attrib_val = 0
                    if( attrib_val not in oracle_kb[ concept ][ attribute ][ 'norm_counts' ] ):
                        continue
                    ####
                    if( attribute not in kb[ concept ] ):
                        kb[ concept ][ attribute ] = {}
                        kb[ concept ][ attribute ][ 'norm_counts' ] = {}
                        kb[ concept ][ attribute ][ 'norm_weights' ] = {}
                    if( attrib_val not in kb[ concept ][ attribute ][ 'norm_counts' ] ):
                        kb[ concept ][ attribute ][ 'norm_counts' ][ attrib_val ] = 0
                        kb[ concept ][ attribute ][ 'norm_weights' ][ attrib_val ] = 0
                    kb[ concept ][ attribute ][ 'norm_counts' ][ attrib_val ] += 1
                    kb[ concept ][ attribute ][ 'norm_weights' ][ attrib_val ] += weight
        ################
        if( args.votingUnit == 'sentence' or
            args.votingUnit == 'span' ):
            for span in kb:
                for cui in kb[ span ][ 'norm_counts' ]:
                    cui_count = kb[ span ][ 'norm_counts' ][ cui ]
                    cui_weight = kb[ span ][ 'norm_weights' ][ cui ]
                    if( cui_count == 0 ):
                        continue
                    modifiers = [ 'confidence={}'.format( cui_count / len( classifiers ) ) ,
                                  'weighted_confidence={}'.format( int( cui_weight ) / len( classifiers ) ) ]
                    if( cui == 'span' ):
                        note_nlp = NoteNlp( begin = kb[ span ][ 'begin_offset' ] ,
                                            end = kb[ span ][ 'end_offset' ] ,
                                            offset = kb[ span ][ 'begin_offset' ] ,
                                            nlp_system = 'Oracle Ensemble System' ,
                                            term_modifiers = ';'.join( modifiers ) )
                    else:
                        note_nlp = NoteNlp( begin = kb[ span ][ 'begin_offset' ] ,
                                            end = kb[ span ][ 'end_offset' ] ,
                                            offset = kb[ span ][ 'begin_offset' ] ,
                                            nlp_system = 'Oracle Ensemble System' ,
                                            note_nlp_source_concept_id = cui ,
                                            term_modifiers = ';'.join( modifiers ) )
                    cas.add_annotation( note_nlp )
        elif( args.votingUnit == 'doc' ):
            for concept in kb:
                concept_count = kb[ concept ][ 'norm_counts' ]
                concept_weight = kb[ concept ][ 'norm_weights' ]
                ## TODO - Current scoring can only support a single key/value
                ## pair in the term_modifiers attribute
                ##modifiers = [ 'confidence={}'.format( int( concept_count ) / len( classifiers ) ) ,
                ##              'weighted_confidence={}'.format( int( concept_weight ) / len( classifiers ) ) ]
                modifiers = []
                term_exists = True
                if( 'polarity' in kb[ concept ] ):
                    ## If we failed to have a valid reference point, leave the default
                    if( 'polarity' in kb[ concept ] ):
                        for attrib_val in kb[ concept ][ 'polarity' ][ 'norm_counts' ]:
                            ## TODO - add error check. this loop should run exactly and only once
                            ##modifiers.append( 'polarity={}'.format( int( attrib_val ) ) )
                            if( int( attrib_val ) == -1 ):
                                term_exists = False
                if( 'uncertainty' in attribute_list ):
                    ## If we failed to have a valid reference point, choose the default
                    if( 'uncertainty' not in kb[ concept ] ):
                        modifiers.append( 'uncertainty={}'.format( 0 ) )
                    else:
                        for attrib_val in kb[ concept ][ 'uncertainty' ][ 'norm_counts' ]:
                            ## TODO - add error check. this loop should run exactly and only once
                            modifiers.append( 'uncertainty={}'.format( int( attrib_val ) ) )
                note_nlp = NoteNlp( begin = 0 ,
                                    end = 0 ,
                                    offset = 0 ,
                                    nlp_system = 'Oracle Ensemble System' ,
                                    note_nlp_source_concept_id = concept ,
                                    term_exists = term_exists ,
                                    term_modifiers = ';'.join( modifiers ) )
                cas.add_annotation( note_nlp )
        if( args.refDir is not None ):
            ref_cas.to_xmi( path = os.path.join( args.refDir , xmi_filename ) ,
                            pretty_print = True )
        if( args.outputDir is not None ):
            cas.to_xmi( path = os.path.join( args.outputDir , xmi_filename ) ,
                        pretty_print = True )



if __name__ == '__main__':
    parser = argparse.ArgumentParser( description = 'Simple oracle ensemble system' )
    parser.add_argument( '-v' , '--verbose' ,
                         help = "Log at the DEBUG level" ,
                         action = "store_true" )
    parser.add_argument( '--types-dir' ,
                         dest = 'typesDir' ,
                         help = 'Directory containing the systems files need to be loaded' )
    parser.add_argument( '--input-dir' ,
                         required = True ,
                         dest = 'inputDir' ,
                         help = 'Input directory containing CAS XMI files' )
    parser.add_argument( '--file-list' ,
                         default = None ,
                         dest = 'fileList' ,
                         help = 'File containing the basename of all files in order' )
    parser.add_argument( '--classifier-list' , nargs = '+' ,
                         default = None ,
                         dest = 'classifierList' ,
                         help = 'List of classifiers (space separated and by numerical id) to include' )
    parser.add_argument( '--voting-unit' ,
                         default = 'span' ,
                         choices = [ 'span' , 'doc' ] ,
                         dest = 'votingUnit' ,
                         help = 'The unit that accumulates votes: "span" means to treat annotations as their own unit, "sentence" means to converge on all spans matching a sentence, "doc" aggregates all annotations at the document level' )
    parser.add_argument( '--ref-dir' ,
                         default = None ,
                         dest = 'refDir' ,
                         help = 'Output directory for writing the reference CAS XMI files to' )
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
        log.basicConfig( format="%(levelname)s: %(message)s" )
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
