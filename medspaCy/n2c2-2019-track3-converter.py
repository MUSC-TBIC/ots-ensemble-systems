import argparse
import glob
import os
import re

from tqdm import tqdm

import spacy
import medspacy
import cassis

from libTypeSystem import metadata_typeString, umlsConcept_typeString

def main( args ):
    teams = [ os.path.basename( f ) for f in glob.glob( os.path.join( args.inputSysDir ,
                                                                      '*.txt' ) ) ]
    ## Load an clinical English medspaCy model trained on i2b2 data
    ## - https://github.com/medspacy/sectionizer/blob/master/notebooks/00-clinical_sectionizer.ipynb
    nlp_pipeline = spacy.load( 'en_info_3700_i2b2_2012' )
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
    NoteMetadata = typesystem.create_type( name = metadata_typeString ,
                                           supertypeName = 'uima.tcas.Annotation' )
    ## TODO - how to represent pairs, as per the reference standard?
    typesystem.add_feature( type_ = NoteMetadata ,
                            name = 'other' ,
                            description = '' ,
                            rangeTypeName = 'uima.cas.String' )
    ############
    ## ... for UmlsConcept
    UmlsConcept = typesystem.create_type( name = umlsConcept_typeString ,
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
    ############################
    ## Iterate over the files, covert to CAS, and write the XMI to disk
    filenames = []
    with open( args.fileList , 'r' ) as fp:
        for line in fp:
            line = line.strip()
            filenames.append( line )
    ##
    oracle_watermark = 0
    oracle_first_norm = {}
    oracle_last_norm = {}
    oracle_norm_size = {}
    for filename in tqdm( filenames ):
        norm_filename = '{}.norm'.format( filename )
        xmi_filename = '{}.xmi'.format( filename )
        with open( os.path.join( args.inputTextDir , '{}.txt'.format( filename ) ) , 'r' ) as fp:
            note_contents = fp.read()
        cas = cassis.Cas( typesystem = typesystem )
        cas.sofa_string = note_contents
        cas.sofa_mime = "text/plain"
        sectionized_note = nlp_pipeline( note_contents )
        team_id = 0
        cas.add_annotation( NoteMetadata( other = '{}={}'.format( 'Oracle' , team_id ) ) )
        for team in sorted( teams ):
            team_id += 1
            cas.add_annotation( NoteMetadata( other = '{}={}'.format( team , team_id ) ) )
        ########################
        ## Tokens
        ## - https://spacy.io/api/token
        #for token in sectionized_note:
        #    cas.add_annotation( TokenAnnotation( begin = token.idx , 
        #                                         end = token.idx + token.__len__() ,
        #                                         text = token.text ) )
        ########################
        ## Oracle Annotations
        ## -
        annot_count = -1
        annot_begins = {}
        annot_ends = {}
        oracle_first_norm[ filename ] = oracle_watermark
        with open( os.path.join( args.inputNormDir , norm_filename ) , 'r' ) as fp:
            for line in fp:
                line = line.strip()
                annot_count += 1
                ## TODO - this treats discontinous spans as a single span from the
                ##        first begin to the last end offsets
                ##        0038    N158||C0085606||975||982||995||1002 ->
                ##        0038    N158||C0085606||975||1002
                ## Known problematic annotation pair introduced by this simplification:
                ##
                ##   test_norm/523704694.norm:
                ##     N214||C0230330||5083||5093||5104||5113
                ##     N215||C0230416||5083||5087||5098||5113
                cols = line.split( '||' )
                norm_id = cols[ 0 ]
                cui = cols[ 1 ]
                begin_offset = cols[ 2 ]
                end_offset = cols[ -1 ]
                annot_begins[ oracle_watermark + annot_count ] = begin_offset
                annot_ends[ oracle_watermark + annot_count ] = end_offset
                ## TODO - Should a UMLS concept be uniquely represented once?
                umls_concept = UmlsConcept( cui = cui )
                ## TODO - convert concepts to concept arrays
                cas.add_annotation( umls_concept )
                concept_id = umls_concept.xmiID
                identified_annotation = IdentifiedAnnotation( begin = begin_offset ,
                                                              end = end_offset ,
                                                              ontologyConceptArray = concept_id ,
                                                              discoveryTechnique = '0' )
                cas.add_annotation( identified_annotation )
        oracle_norm_size[ filename ] = annot_count
        oracle_watermark += annot_count
        oracle_last_norm[ filename ] = oracle_watermark
        team_id = 0
        for team in sorted( teams ):
            team_id += 1
            team_filename = os.path.join( args.inputSysDir ,
                                          team )
            with open( team_filename , 'r' ) as team_fp:
                line_count = -1
                for line in team_fp:
                    line_count += 1
                    if( line_count < oracle_first_norm[ filename ] ):
                        continue
                    elif( line_count > oracle_last_norm[ filename ] ):
                        break
                    line = line.strip()
                    umls_concept = UmlsConcept( cui = line )
                    cas.add_annotation( umls_concept )
                    concept_id = umls_concept.xmiID
                    identified_annotation = IdentifiedAnnotation( begin = annot_begins[ line_count ] ,
                                                                  end = annot_ends[ line_count ] ,
                                                                  ontologyConceptArray = concept_id ,
                                                                  discoveryTechnique = team_id )
                    cas.add_annotation( identified_annotation )
        cas.to_xmi( path = os.path.join( args.outputDir , xmi_filename ) ,
                    pretty_print = True )
        oracle_watermark += 1

if __name__ == '__main__':
    parser = argparse.ArgumentParser( description = 'Simple spaCy pipeline for converting n2c2 2019 Track 3 to CAS XMI files with a SHARP-n schema' )
    parser.add_argument( '--input-text' ,
                         dest = 'inputTextDir' ,
                         help = 'Input directory containing plain text files' )
    parser.add_argument( '--input-norm' ,
                         dest = 'inputNormDir' ,
                         help = 'Input directory containing normalized files' )
    parser.add_argument( '--input-systems' ,
                         dest = 'inputSysDir' ,
                         help = 'Input directory containing the system output file' )
    parser.add_argument( '--file-list' ,
                         dest = 'fileList' ,
                         help = 'File containing the basename of all files in order' )
    parser.add_argument( '--output-dir' ,
                         dest = 'outputDir' ,
                         help = 'Output directory for writing CAS XMI files to' )
    args = parser.parse_args()
    main( args )
