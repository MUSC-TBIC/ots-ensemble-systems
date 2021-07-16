import argparse
import glob
import os
import re

from tqdm import tqdm

import spacy
import medspacy
import cassis

top10_offset = {}

def main( inputDir , outputDir ):
    teams = [ os.path.basename( f ) for f in glob.glob( os.path.join( inputDir ,
                                                                      '..' ,
                                                                      '..' ,
                                                                      'top10_outputs' ,
                                                                      '*.txt' ) ) ]
    for team in teams:
        top10_offset[ team ] = -1
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
    filenames = [ os.path.basename( f ) for f in glob.glob( os.path.join( inputDir ,
                                                                          '*.txt' ) ) ]
    for filename in tqdm( filenames ):
        if( filename != '0034.txt' ):
            continue
        norm_filename = re.sub( '.txt$' ,
                                '.norm' ,
                                filename )
        xmi_filename = re.sub( '.txt$' ,
                               '.xmi' ,
                               filename )
        with open( os.path.join( inputDir , filename ) , 'r' ) as fp:
            note_contents = fp.read()
        cas = cassis.Cas( typesystem = typesystem )
        cas.sofa_string = note_contents
        cas.sofa_mime = "text/plain"
        sectionized_note = nlp_pipeline( note_contents )
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
        with open( os.path.join( inputDir , '..' , 'train_norm' , norm_filename ) , 'r' ) as fp:
            for line in fp:
                line = line.strip()
                annot_count += 1
                norm_id , cui , begin_offset , end_offset = line.split( '||' )
                annot_begins[ annot_count ] = begin_offset
                annot_ends[ annot_count ] = end_offset
                umls_concept = UmlsConcept( cui = cui )
                cas.add_annotation( umls_concept )
                concept_id = umls_concept.xmiID
                identified_annotation = IdentifiedAnnotation( begin = begin_offset ,
                                                              end = end_offset ,
                                                              ontologyConceptArray = concept_id ,
                                                              discoveryTechnique = '0' )
                cas.add_annotation( identified_annotation )
        team_id = 0
        for team in sorted( teams ):
            team_id += 1
            team_filename = os.path.join( inputDir ,
                                          '..' ,
                                          '..' ,
                                          'top10_outputs' ,
                                          team )
            with open( team_filename , 'r' ) as team_fp:
                line_count = -1
                for line in team_fp:
                    line_count += 1
                    if( line_count <= top10_offset[ team ] ):
                        next
                    elif( line_count > annot_count ):
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
                top10_offset[ team ] = line_count
        cas.to_xmi( path = os.path.join( outputDir , xmi_filename ) ,
                    pretty_print = True )

if __name__ == '__main__':
    parser = argparse.ArgumentParser( description = 'Simple spaCy pipeline for converting n2c2 2019 Track 3 to CAS XMI files with a SHARP-n schema' )
    parser.add_argument( 'inputDir' ,
                         help = 'Input directory containing plain text files to split' )
    parser.add_argument( 'outputDir' ,
                         help = 'Output directory for writing CAS XMI files to' )
    args = parser.parse_args()
    main( os.path.abspath( args.inputDir ) ,
          os.path.abspath( args.outputDir ) )
