import argparse
import glob
import os
import re

from tqdm import tqdm

import spacy
import medspacy
import cassis

from lxml import etree as ET

from libTypeSystem import metadata_typeString

def process_ann_file( cas , IdentifiedAnnotation ,
                      input_filename ,
                      classifier_id ):
    with open( input_filename , 'r' ) as fp:
        for line in fp:
            line = line.strip()
            ## Continuous:
            ## T1    Organization 0 43    International Business Machines Corporation
            ## Discontinuous (0..23):
            ## T1	Location 0 5;16 23	North America
            ## T1	Location 0 5;8 12;16 23	North America
            ## TODO - add flag to accommodate different scoring styles for
            ##        discontinuous spans.  Current approach treats these
            ##        spans as equivalent to the maximal span of all sub-spans.
            matches = re.match( r'^(T[0-9]+)\s+([\w\-]+)\s+([0-9]+)\s+([0-9]+;[0-9]+\s+)*([0-9]+)\s+(.*)' ,
                                line )
            if( matches ):
                found_tag = matches.group( 2 )
                if( found_tag not in [ 'Section' , 'SectionHeader' ] ):
                    continue
                match_index = matches.group( 1 )
                begin_pos = matches.group( 3 )
                end_pos = matches.group( 5 )
                raw_text = matches.group( 6 )
                cas.add_annotation( IdentifiedAnnotation( begin = begin_pos ,
                                                          end = end_pos ,
                                                          discoveryTechnique = classifier_id ) )
    return( cas )


def process_cas_xmi_file( cas , IdentifiedAnnotation ,
                          input_filename ,
                          classifier_id ):
    input_tree = ET.parse( input_filename )
    input_root = input_tree.getroot()
    ##
    for node in input_root:
        if( 'beginHeader' in node.attrib ):
                begin_pos = node.attrib[ 'beginHeader' ]
                end_pos = node.attrib[ 'endHeader' ]
                cas.add_annotation( IdentifiedAnnotation( begin = begin_pos ,
                                                          end = end_pos ,
                                                          discoveryTechnique = classifier_id ) )
    return( cas )


def process_sentence_file( cas , typesystem ,
                           input_filename ):
    SentenceAnnotation = typesystem.get_type( 'org.apache.ctakes.typesystem.type.textspan.Sentence' )
    with open( input_filename , 'rb' ) as fp:
        ref_cas = cassis.load_cas_from_xmi( fp ,
                                            typesystem = typesystem )
    for sentence in ref_cas.select( 'textsem.Sentence' ):
        cas.add_annotation( SentenceAnnotation( begin = sentence.begin ,
                                                end = sentence.end ) )
    return( cas )

                
def process_bionlp_file( cas , IdentifiedAnnotation ,
                         input_filename ,
                         classifier_id ):
    input_tree = ET.parse( input_filename )
    input_root = input_tree.getroot()
    ##
    for node in input_root:
        for child_node in node:
            print( '{}'.format( child_node ) )
            if( 'Type' in child_node.attrib and
                child_node.attrib[ 'Type' ] == 'Section' ):
                begin_pos = child_node.attrib[ 'Start' ]
                end_pos = child_node.attrib[ 'Start' ]
                cas.add_annotation( IdentifiedAnnotation( begin = begin_pos ,
                                                          end = end_pos ,
                                                          discoveryTechnique = classifier_id ) )
    return( cas )

                
def main( args ):
    ## Load an clinical English medspaCy model trained on i2b2 data
    ## - https://github.com/medspacy/sectionizer/blob/master/notebooks/00-clinical_sectionizer.ipynb
    nlp = spacy.load('en_info_3700_i2b2_2012')
    ############################
    ## Iterate over the files to create coverage map
    txt_filenames = [ os.path.basename( f ) for f in glob.glob( os.path.join( args.inputRefDir ,
                                                                              '*.txt' ) ) ]
    if( args.inputSharpnDir is None ):
        teams = []
    else:
        teams = [ os.path.basename( f ) for f in glob.glob( os.path.join( args.inputSharpnDir ,
                                                                          '*' ) ) ]
    if( args.inputBionlpDir is not None ):
        for new_team in [ os.path.basename( f ) for f in glob.glob( os.path.join( args.inputBionlpDir ,
                                                                                  '*' ) ) ]:
            teams.append( new_team )
    ############################
    ## Create a type system
    ## - https://github.com/dkpro/dkpro-cassis/blob/master/cassis/typesystem.py
    with open( os.path.join( args.typesDir , 'Sentence.xml' ) , 'rb' ) as fp:
        typesystem = cassis.load_typesystem( fp )
    SentenceAnnotation = typesystem.get_type( 'org.apache.ctakes.typesystem.type.textspan.Sentence' )
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
    ## ... for sections (and, by association, section headers)
    NoteSection = typesystem.create_type( name = 'edu.musc.tbic.uima.NoteSection' ,
                                          supertypeName = 'uima.tcas.Annotation' )
    typesystem.add_feature( type_ = NoteSection ,
                            name = 'SectionNumber' ,
                            description = '' ,
                            rangeTypeName = 'uima.cas.Integer' )
    typesystem.add_feature( type_ = NoteSection ,
                            name = 'SectionDepth' ,
                            description = 'Given an hierarchical section schema, how deep is the current section ( 0 = root level/major category)' , 
                            rangeTypeName = 'uima.cas.Integer' )
    typesystem.add_feature( type_ = NoteSection ,
                            name = 'SectionId' ,
                            description = 'Type (or concept id) of current section' , 
                            rangeTypeName = 'uima.cas.String' )
    typesystem.add_feature( type_ = NoteSection ,
                            name = 'beginHeader' ,
                            description = 'The start offset for this section\'s header (-1 if no header)' , 
                            rangeTypeName = 'uima.cas.Integer' )
    typesystem.add_feature( type_ = NoteSection ,
                            name = 'endHeader' ,
                            description = 'The end offset for this section\'s header (-1 if no header)' , 
                            rangeTypeName = 'uima.cas.Integer' )
    typesystem.add_feature( type_ = NoteSection ,
                            name = 'modifiers' ,
                            description = 'Modifiers (key/value pairs) associated with the given section' , 
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
    for txt_filename in tqdm( txt_filenames ):
        ann_filename = re.sub( '.txt$' , '.ann' , txt_filename )
        xmi_filename = re.sub( '.txt$' , '.xmi' , txt_filename )
        xml_filename = re.sub( '.txt$' , '.xml' , txt_filename )
        with open( os.path.join( args.inputRefDir , txt_filename ) , 'r' ) as fp:
            note_contents = fp.read()
        cas = cassis.Cas( typesystem = typesystem )
        cas.sofa_string = note_contents
        cas.sofa_mime = "text/plain"
        team_id = 0
        cas.add_annotation( NoteMetadata( other = '{}={}'.format( 'Oracle' , team_id ) ) )
        for team in sorted( teams ):
            team_id += 1
            cas.add_annotation( NoteMetadata( other = '{}={}'.format( team , team_id ) ) )
        #### split sentences
        ## We can automatically add sentences processed here if we haven't been
        ## given any other directive...
        if( args.inputSentenceDir is None or
            not os.path.exists( os.path.join( args.inputSentenceDir , xmi_filename ) ) ):
            processed_notes = nlp( note_contents )
            for sent_i , sent in enumerate( processed_notes.sents ):
                cas.add_annotation( SentenceAnnotation( begin = sent.start ,
                                                        end = sent.end ,
                                                        sentenceNumber = sent_i ) )
        else:
            ## Or we can load in sentence annotations from an external system
            cas = process_sentence_file( cas ,
                                         typesystem ,
                                         os.path.exists( os.path.join( args.inputSentenceDir , xmi_filename ) ) )
        ####
        team_id = 0
        cas = process_ann_file( cas ,
                                IdentifiedAnnotation ,
                                os.path.join( args.inputRefDir , ann_filename ) ,
                                team_id )
        ####
        for team in sorted( teams ):
            team_id += 1
            if( args.inputSharpnDir is not None and
                os.path.exists( os.path.join( args.inputSharpnDir , team , xmi_filename ) ) ):
                cas = process_cas_xmi_file( cas ,
                                            IdentifiedAnnotation ,
                                            os.path.join( args.inputSharpnDir , team , xmi_filename ) ,
                                            team_id )
                
            elif( args.inputBionlpDir is not None and
                  os.path.exists( os.path.join( args.inputBionlpDir , team , xml_filename ) ) ):
                cas = process_bionlp_file( cas ,
                                           IdentifiedAnnotation ,
                                           os.path.join( args.inputBionlpDir , team , xml_filename ) ,
                                           team_id )
        ####
        cas.to_xmi( path = os.path.join( args.outputDir , xmi_filename ) ,
                    pretty_print = True )



if __name__ == '__main__':
    parser = argparse.ArgumentParser( description = 'Simple spaCy pipeline for converting various sectionizer outputs to CAS XMI files with a SHARP-n schema' )
    parser.add_argument( '--types-dir' ,
                         dest = 'typesDir' ,
                         help = 'Directory containing the systems files need to be loaded' )
    parser.add_argument( '--input-ref-dir' ,
                         dest = 'inputRefDir' ,
                         help = 'Input directory containing plain text and brat .ann files' )
    parser.add_argument( '--input-sentence-dir' , default = None ,
                         dest = 'inputSentenceDir' ,
                         help = 'Input directory containing Sentence annotations in SHARPn-style schema' )
    parser.add_argument( '--input-sharpn-systems' , default = None ,
                         dest = 'inputSharpnDir' ,
                         help = 'Input directory containing the system output files in a SHARPn-style schema' )
    parser.add_argument( '--input-bionlp-systems' , default = None ,
                         dest = 'inputBionlpDir' ,
                         help = 'Input directory containing the system output files in a BioNLP-style schema' )
    parser.add_argument( '--output-dir' ,
                         dest = 'outputDir' ,
                         help = 'Output directory for writing CAS XMI files to' )
    args = parser.parse_args()
    if( not os.path.exists( args.outputDir ) ):
        try:
            os.makedirs( args.outputDir )
        except OSError as e:
            log.error( 'OSError caught while trying to create output folder:  {}'.format( e ) )
        except IOError as e:
            log.error( 'IOError caught while trying to create output folder:  {}'.format( e ) )
    main( args )
