import argparse
import glob
import os
import re

from tqdm import tqdm

import spacy
import medspacy
import cassis

## TODO - refactor type system creation to be importable from a separate file

def main( args , classifiers ):
    ############################
    ## Create a type system
    ## - https://github.com/dkpro/dkpro-cassis/blob/master/cassis/typesystem.py
    ############
    ## ... for tokens
    typesystem = cassis.TypeSystem()
    TokenAnnotation = typesystem.create_type( name = 'uima.tt.TokenAnnotation' , 
                                              supertypeName = 'uima.tcas.Annotation' )
    typesystem.add_feature( type_ = TokenAnnotation ,
                            name = 'text' , 
                            rangeTypeName = 'uima.cas.String' )
    ############
    ## ... for Metadata
    ## TODO - this parent and supertype should probably be something else
    NoteMetadata = typesystem.create_type( name = 'refsem.Metadata' ,
                                           supertypeName = 'uima.tcas.Annotation' )
    ## TODO - how to represent pairs, as per the reference standard?
    typesystem.add_feature( type_ = NoteMetadata ,
                            name = 'other' ,
                            description = '' ,
                            rangeTypeName = 'uima.cas.String' )
    ############
    ## ... for UmlsConcept
    UmlsConcept = typesystem.create_type( name = 'refsem.UmlsConcept' ,
                                          supertypeName = 'uima.tcas.Annotation' )
    typesystem.add_feature( type_ = UmlsConcept ,
                            name = 'tui' ,
                            description = '' ,
                            rangeTypeName = 'uima.cas.String' )
    typesystem.add_feature( type_ = UmlsConcept ,
                            name = 'cui' ,
                            description = '' ,
                            rangeTypeName = 'uima.cas.String' )
    ############
    ## ... for IdentifiedAnnotation
    IdentifiedAnnotation = typesystem.create_type( name = 'textsem.IdentifiedAnnotation' ,
                                                   supertypeName = 'uima.tcas.Annotation' )
    typesystem.add_feature( type_ = IdentifiedAnnotation ,
                            name = 'ontologyConceptArray' ,
                            description = 'The xmi:id of the array of ontology concepts associated with this annotation' ,
                            rangeTypeName = 'uima.cas.Integer' )
    typesystem.add_feature( type_ = IdentifiedAnnotation ,
                            name = 'discoveryTechnique' ,
                            description = 'The index of the discovery technique (or classifier) that produced this annotation' ,
                            rangeTypeName = 'uima.cas.Integer' )
    typesystem.add_feature( type_ = IdentifiedAnnotation ,
                            name = 'confidence' ,
                            description = 'A confidence score [0-1] generated by the discoveryTechnique when generating producing this annotation' ,
                            rangeTypeName = 'uima.cas.Double' )
    ############
    ## ... for OMOP CDM v5.3 NOTE_NLP table properties
    NoteNlp = typesystem.create_type( name = 'edu.musc.tbic.omop_cdm.Note_Nlp_TableProperties' ,
                                      supertypeName = 'uima.tcas.Annotation' )
    typesystem.add_feature( type_ = NoteNlp ,
                            name = 'note_id' ,
                            description = '' ,
                            rangeTypeName = 'uima.cas.Integer' )
    typesystem.add_feature( type_ = NoteNlp ,
                            name = 'section_concept_id' ,
                            description = '' ,
                            rangeTypeName = 'uima.cas.Integer' )
    typesystem.add_feature( type_ = NoteNlp ,
                            name = 'snippet' ,
                            description = '' ,
                            rangeTypeName = 'uima.cas.String' )
    typesystem.add_feature( type_ = NoteNlp ,
                            name = 'offset' ,
                            description = '' ,
                            rangeTypeName = 'uima.cas.Integer' )
    typesystem.add_feature( type_ = NoteNlp ,
                            name = 'lexical_variant' ,
                            description = '' ,
                            rangeTypeName = 'uima.cas.String' )
    typesystem.add_feature( type_ = NoteNlp ,
                            name = 'note_nlp_concept_id' ,
                            description = '' ,
                            rangeTypeName = 'uima.cas.Integer' )
    ## TODO - this really should be an int but we can't look up the appropriate
    ##        ID without a connected OMOP CDM Concept table
    typesystem.add_feature( type_ = NoteNlp ,
                            name = 'note_nlp_source_concept_id' ,
                            description = '' ,
                            rangeTypeName = 'uima.cas.String' )
    typesystem.add_feature( type_ = NoteNlp ,
                            name = 'nlp_system' ,
                            description = '' ,
                            rangeTypeName = 'uima.cas.String' )
    typesystem.add_feature( type_ = NoteNlp ,
                            name = 'term_exists' ,
                            description = '' ,
                            rangeTypeName = 'uima.cas.String' )
    typesystem.add_feature( type_ = NoteNlp ,
                            name = 'term_temporal' ,
                            description = '' ,
                            rangeTypeName = 'uima.cas.String' )
    typesystem.add_feature( type_ = NoteNlp ,
                            name = 'term_modifiers' ,
                            description = '' ,
                            rangeTypeName = 'uima.cas.String' )
    ############################
    ## Iterate over the files, covert to CAS, and write the XMI to disk
    filenames = []
    with open( args.fileList , 'r' ) as fp:
        for line in fp:
            line = line.strip()
            filenames.append( line )
    ##
    for filename in tqdm( filenames ,
                          desc = 'Oracle' ):
        ##
        classifier2id = {}
        id2classifier = {}
        xmiId2cui = {}
        ##
        xmi_filename = '{}.xmi'.format( filename )
        with open( os.path.join( args.inputDir , xmi_filename ) , 'rb' ) as fp:
            ref_cas = cassis.load_cas_from_xmi( fp ,
                                                typesystem = typesystem )
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
        ## Grab all...
        kb = {}
        oracle_kb = {}
        for annot in cas.select( 'textsem.IdentifiedAnnotation' ):
            technique = annot.discoveryTechnique
            concept_id = int( annot.ontologyConceptArray )
            cui = xmiId2cui[ concept_id ]
            begin_offset = annot.begin
            end_offset = annot.end
            span = '{}-{}'.format( begin_offset , end_offset )
            if( technique == '0' ):
                oracle_kb[ span ] = {}
                oracle_kb[ span ][ 'begin_offset' ] = begin_offset
                oracle_kb[ span ][ 'end_offset' ] = end_offset
                oracle_kb[ span ][ 'norm_counts' ] = {}
                oracle_kb[ span ][ 'norm_weights' ] = {}
                oracle_kb[ span ][ 'norm_counts' ][ cui ] = 1
                oracle_kb[ span ][ 'norm_weights' ][ cui ] = 1
                note_nlp = NoteNlp( begin = begin_offset ,
                                    end = end_offset ,
                                    offset = begin_offset ,
                                    nlp_system = 'Reference Standard' ,
                                    note_nlp_source_concept_id = cui )
                ref_cas.add_annotation( note_nlp )
            elif( technique in classifiers ):
                if( span not in kb ):
                    kb[ span ] = {}
                    kb[ span ][ 'begin_offset' ] = begin_offset
                    kb[ span ][ 'end_offset' ] = end_offset
                    kb[ span ][ 'norm_counts' ] = {}
                    kb[ span ][ 'norm_weights' ] = {}
                if( cui not in kb[ span ][ 'norm_counts' ] ):
                    kb[ span ][ 'norm_counts' ][ cui ] = 0
                    kb[ span ][ 'norm_weights' ][ cui ] = 0
                if( cui in oracle_kb[ span ][ 'norm_counts' ] ):
                    kb[ span ][ 'norm_counts' ][ cui ] += 1
                    kb[ span ][ 'norm_weights' ][ cui ] += 1
        for span in kb:
            for cui in kb[ span ][ 'norm_counts' ]:
                cui_count = kb[ span ][ 'norm_counts' ][ cui ]
                if( cui_count == 0 ):
                    continue
                note_nlp = NoteNlp( begin = kb[ span ][ 'begin_offset' ] ,
                                    end = kb[ span ][ 'end_offset' ] ,
                                    offset = kb[ span ][ 'begin_offset' ] ,
                                    nlp_system = 'Oracle Ensemble System' ,
                                    note_nlp_source_concept_id = cui ,
                                    term_modifiers = 'confidence={}'.format( cui_count / len( classifiers ) ) )
                cas.add_annotation( note_nlp )
        if( args.refDir is not None ):
            ref_cas.to_xmi( path = os.path.join( args.refDir , xmi_filename ) ,
                            pretty_print = True )
        if( args.outputDir is not None ):
            cas.to_xmi( path = os.path.join( args.outputDir , xmi_filename ) ,
                        pretty_print = True )



if __name__ == '__main__':
    parser = argparse.ArgumentParser( description = 'Simple oracle ensemble system' )
    parser.add_argument( '--input-dir' ,
                         required = True ,
                         dest = 'inputDir' ,
                         help = 'Input directory containing CAS XMI files' )
    parser.add_argument( '--file-list' ,
                         required = True ,
                         dest = 'fileList' ,
                         help = 'File containing the basename of all files in order' )
    parser.add_argument( '--classifier-list' ,
                         default = '1234567890' ,
                         dest = 'classifierList' ,
                         help = 'List of classifiers (by id) to include' )
    parser.add_argument( '--ref-dir' ,
                         default = None ,
                         dest = 'refDir' ,
                         help = 'Output directory for writing the reference CAS XMI files to' )
    parser.add_argument( '--output-dir' ,
                         default = None ,
                         dest = 'outputDir' ,
                         help = 'Output directory for writing the oracle consolidated CAS XMI files to' )
    args = parser.parse_args()
    classifiers = []
    for i in range( 0 , len( args.classifierList ) ):
        if( args.classifierList[ i ] == '0' ):
            classifiers.append( '10' )
        else:
            classifiers.append( args.classifierList[ i ] )
    main( args , classifiers )
