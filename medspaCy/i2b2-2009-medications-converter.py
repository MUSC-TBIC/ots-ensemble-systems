import argparse
import glob
import os
import re

import logging as log

from tqdm import tqdm

import spacy
import medspacy
import cassis

def process_line( note_contents , line ):
    cols = line.split( '||' )
    medications = cols[ 0 ]
    begin_lineToks , end_lineToks = medications.split( ' ' )[ -2: ]
    try:
        begin_line , begin_tok = begin_lineToks.split( ':' )
    except ValueError as e:
        ## TODO - discontinous annotations:
        ## m="long ... acting ... insulin" 115:9 115:9,116:0 116:0,116:2 116:2
        ## m="short-acting ... insulin" 116:0 116:0,116:2 116:2
        return( -1 , -1 )
    begin_line = int( begin_line ) - 1
    begin_tok = int( begin_tok )
    end_line , end_tok = end_lineToks.split( ':' )
    end_line = int( end_line ) - 1
    end_tok = int( end_tok )
    begin_line_offset = 0
    begin_token_offset = 0
    if( begin_line > 0 ):
        begin_line_offset = 1 + len( '\n'.join( note_contents[ 0:begin_line ] ) )
    note_line = note_contents[ begin_line ]
    line_tokens = note_line.split()
    if( begin_tok > 0 ):
        begin_token_offset = 1 + len( ' '.join( line_tokens[ 0:begin_tok ] ) )
    begin_offset = begin_line_offset + begin_token_offset
    end_line_offset = 0
    end_token_offset = 0
    if( begin_line == end_line ):
        if( begin_tok == end_tok ):
            try:
                end_token_offset = len( line_tokens[ begin_tok ] )
            except IndexError as e:
                ## TODO - Error on line:
                ## m="famciclovir" 75:9 75:9
                log.error( 'IndexError in line. begin_tok={} while len( line_tokens )={}'.format( begin_tok , len( line_tokens ) ) )
        else:
            end_token_offset = len( ' '.join( line_tokens[ begin_tok:( end_tok + 1 ) ] ) )
    else:
        ## Add the end of the "begin" line
        end_token_offset = len( ' '.join( line_tokens[ begin_tok: ] ) )
        ## Grab the "end" line
        note_line = note_contents[ end_line ]
        line_tokens = note_line.split()
        ## Calculate characters from the start of this line to the end of the end token
        end_token_offset += 1 + len( ' '.join( line_tokens[ 0:( end_tok + 1 ) ] ) )
        ## Calculate the length of all intervening lines
        if( end_line - begin_line > 1 ):
            end_line_offset = 1 + len( '\n'.join( note_contents[ ( begin_line + 1 ):end_line ] ) )
    end_offset = begin_offset + end_line_offset + end_token_offset
    return( begin_offset , end_offset )
    

def main( args ):
    teams = [ os.path.basename( f ) for f in glob.glob( os.path.join( args.inputSysDir ,
                                                                      '*' ) ) ]
    for team in sorted( teams ):
        print( '{}'.format( team ) )
    
    ############################
    ## Iterate over the files to create coverage map
    txt_filenames = [ os.path.basename( f ) for f in glob.glob( os.path.join( args.inputTextDir ,
                                                                              '*' ) ) ]
    ref_mapping  = {}
    team_coverage_mapping = {}
    m_filenames = [ os.path.basename( f ) for f in glob.glob( os.path.join( args.inputRefDir ,
                                                                            '*.m' ) ) ]
    for m in m_filenames:
        file_details = m.split( '.' )
        if( file_details[ 0 ] in txt_filenames ):
            ref_mapping[ file_details[ 0 ] ] = m
    for txt_filename in txt_filenames:
        team_coverage_mapping[ txt_filename ] = []
        for team in sorted( teams ):
            if( os.path.exists( os.path.join( args.inputSysDir ,
                                              team ,
                                              '{}.i2b2.entries'.format( txt_filename ) ) ) ):
                team_coverage_mapping[ txt_filename ].append( team )
    ############################
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
    ############################
    ## Iterate over the files, covert to CAS, and write the XMI to disk
    oracle_watermark = 0
    oracle_first_norm = {}
    oracle_last_norm = {}
    oracle_norm_size = {}
    for txt_filename in tqdm( txt_filenames ):
        note_contents = []
        xmi_filename = '{}.xmi'.format( txt_filename )
        with open( os.path.join( args.inputTextDir , txt_filename ) , 'r' ) as fp:
            for line in fp:
                line = line.strip()
                note_contents.append( line )
        cas = cassis.Cas( typesystem = typesystem )
        cas.sofa_string = '\n'.join( note_contents )
        cas.sofa_mime = "text/plain"
        sectionized_note = nlp_pipeline( cas.sofa_string )
        team_id = 0
        if( txt_filename in ref_mapping ):
            cas.add_annotation( NoteMetadata( other = '{}={}'.format( 'Oracle' , team_id ) ) )
        for team in sorted( teams ):
            team_id += 1
            if( team in team_coverage_mapping[ txt_filename ] ):
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
        if( txt_filename in ref_mapping ):
            with open( os.path.join( args.inputRefDir ,
                                     ref_mapping[ txt_filename ] ) ,
                       'r' ) as fp:
                for line in fp:
                    line = line.strip()
                    begin_offset , end_offset = process_line( note_contents , line )
                    if( begin_offset > -1 ):
                        identified_annotation = IdentifiedAnnotation( begin = begin_offset ,
                                                                      end = end_offset ,
                                                                      discoveryTechnique = '0' )
                        cas.add_annotation( identified_annotation )
        team_id = 0
        for team in sorted( teams ):
            team_id += 1
            if( team not in team_coverage_mapping[ txt_filename ] ):
                continue
            team_filename = os.path.join( args.inputSysDir ,
                                          team ,
                                          '{}.i2b2.entries'.format( txt_filename ) )
            with open( team_filename , 'r' ) as team_fp:
                for line in team_fp:
                    line = line.strip()
                    if( line == '' ):
                        continue
                    begin_offset , end_offset = process_line( note_contents , line )
                    if( begin_offset > -1 ):
                        identified_annotation = IdentifiedAnnotation( begin = begin_offset ,
                                                                      end = end_offset ,
                                                                      discoveryTechnique = team_id )
                        cas.add_annotation( identified_annotation )
        cas.to_xmi( path = os.path.join( args.outputDir , xmi_filename ) ,
                    pretty_print = True )


if __name__ == '__main__':
    parser = argparse.ArgumentParser( description = 'Simple spaCy pipeline for converting i2b2 2009 medications challenge to CAS XMI files with a SHARP-n schema' )
    parser.add_argument( '--input-text' ,
                         dest = 'inputTextDir' ,
                         help = 'Input directory containing plain text files' )
    parser.add_argument( '--input-ref' ,
                         dest = 'inputRefDir' ,
                         help = 'Input directory containing reference standard files' )
    parser.add_argument( '--input-systems' ,
                         dest = 'inputSysDir' ,
                         help = 'Input directory containing the system output file' )
    parser.add_argument( '--output-dir' ,
                         dest = 'outputDir' ,
                         help = 'Output directory for writing CAS XMI files to' )
    args = parser.parse_args()
    ## Set up logging
    if args.verbose:
        log.basicConfig( format = "%(levelname)s: %(message)s" ,
                         level = log.DEBUG )
        log.info( "Verbose output." )
        log.debug( "{}".format( args ) )
    else:
        log.basicConfig( format="%(levelname)s: %(message)s" )
    ####
    if( not os.path.exists( args.outputDir ) ):
        try:
            os.makedirs( args.outputDir )
        except OSError as e:
            log.error( 'OSError caught while trying to create output folder:  {}'.format( e ) )
        except IOError as e:
            log.error( 'IOError caught while trying to create output folder:  {}'.format( e ) )
    main( args )
