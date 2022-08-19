import argparse
import glob
import os
import re

import logging as log

from tqdm import tqdm

import spacy
import medspacy
import cassis

import warnings
warnings.filterwarnings( 'ignore' , category = UserWarning , module = 'cassis' )


metadata_typeString = 'org.apache.ctakes.typesystem.type.structured.Metadata'
umlsConcept_typeString = 'org.apache.ctakes.typesystem.type.refsem.UmlsConcept'

identifiedAnnotation_typeString = 'textsem.IdentifiedAnnotation'
eventMention_typeString = 'org.apache.ctakes.typesystem.type.textsem.EventMention'
modifier_typeString = 'org.apache.ctakes.typesystem.type.textsem.Modifier'
timeMention_typeString = 'org.apache.ctakes.typesystem.type.textsem.TimeMention'

event_typeString = 'org.apache.ctakes.typesystem.type.refsem.Event'
eventProperties_typeString = 'org.apache.ctakes.typesystem.type.refsem.EventProperties'
attribute_typeString = 'org.apache.ctakes.typesystem.type.refsem.Attribute'

relationArgument_typeString = 'org.apache.ctakes.typesystem.type.relation.RelationArgument'
binaryTextRelation_typeString = 'org.apache.ctakes.typesystem.type.relation.BinaryTextRelation'

noteNlp_typeString = 'edu.musc.tbic.omop_cdm.Note_Nlp_TableProperties'


def loadTypeSystem( typesDir , typesFile = None ):
    ############################
    ## Create a type system
    ## - https://github.com/dkpro/dkpro-cassis/blob/master/cassis/typesystem.py
    if( typesDir is None ):
        with open( typesFile , 'rb' ) as fp:
            typesystem = cassis.load_typesystem( fp )
        ############
        ## ... for Metadata
        NoteMetadata = typesystem.get_type( metadata_typeString )
        ## TODO - how to represent pairs, as per the reference standard?
        ## TODO - why is this missing from cTAKES type system definition?
        typesystem.add_feature( type_ = NoteMetadata ,
                                name = 'other' ,
                                description = '' ,
                                rangeTypeName = 'uima.cas.String' )
    else:
        with open( os.path.join( typesDir , 'Sentence.xml' ) , 'rb' ) as fp:
            typesystem = cassis.load_typesystem( fp )
        SentenceAnnotation = typesystem.get_type( 'org.apache.ctakes.typesystem.type.textspan.Sentence' )
        ############
        ## ... for tokens
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
        IdentifiedAnnotation = typesystem.create_type( name = identifiedAnnotation_typeString ,
                                                       supertypeName = 'uima.tcas.Annotation' )
        typesystem.add_feature( type_ = IdentifiedAnnotation ,
                                name = 'polarity' ,
                                description = 'Default value of 0. Set to 1 when specifically asserted/positive and -1 when the annotation is "stated with negation"' ,
                                rangeTypeName = 'uima.cas.Integer' )
        typesystem.add_feature( type_ = IdentifiedAnnotation ,
                                name = 'uncertainty' ,
                                description = 'A 1 for when the annotation is "stated with doubt"; otherwise a 0' ,
                                rangeTypeName = 'uima.cas.Integer' )
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
    NoteNlp = typesystem.create_type( name = noteNlp_typeString ,
                                      supertypeName = 'uima.tcas.Annotation' )
    typesystem.add_feature( type_ = NoteNlp ,
                            name = 'note_nlp_id' ,
                            description = 'A unique identifier for the NLP record.' ,
                            rangeTypeName = 'uima.cas.Integer' )
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
                            description = 'Term_exists is defined as a flag that indicates if the patient actually has or had the condition. Any of the following modifiers would make Term_exists false: Negation = true; Subject = [anything other than the patient]; Conditional = true; Rule_out = true; Uncertain = very low certainty or any lower certainties. A complete lack of modifiers would make Term_exists true. For the modifiers that are there, they would have to have these values: Negation = false; Subject = patient; Conditional = false; Rule_out = false; Uncertain = true or high or moderate or even low (could argue about low).' ,
                            rangeTypeName = 'uima.cas.Boolean' )
    typesystem.add_feature( type_ = NoteNlp ,
                            name = 'term_temporal' ,
                            description = '' ,
                            rangeTypeName = 'uima.cas.String' )
    typesystem.add_feature( type_ = NoteNlp ,
                            name = 'term_modifiers' ,
                            description = '' ,
                            rangeTypeName = 'uima.cas.String' )
    ############
    ## ... for OMOP CDM v5.3 FACT_RELATIONSHIP table properties
    ##     https://ohdsi.github.io/CommonDataModel/cdm53.html#FACT_RELATIONSHIP
    FactRelationship = typesystem.create_type( name = 'edu.musc.tbic.omop_cdm.Fact_Relationship_TableProperties' ,
                                               supertypeName = 'uima.tcas.Annotation' )
    typesystem.add_feature( type_ = FactRelationship ,
                            name = 'domain_concept_id_1' ,
                            description = 'The CONCEPT id for the appropriate scoping domain' ,
                            rangeTypeName = 'uima.cas.Integer' )
    typesystem.add_feature( type_ = FactRelationship ,
                            name = 'fact_id_1' ,
                            description = 'The id for the first fact' ,
                            rangeTypeName = 'uima.cas.Integer' )
    typesystem.add_feature( type_ = FactRelationship ,
                            name = 'domain_concept_id_2' ,
                            description = 'The CONCEPT id for the appropriate scoping domain' ,
                            rangeTypeName = 'uima.cas.Integer' )
    typesystem.add_feature( type_ = FactRelationship ,
                            name = 'fact_id_2' ,
                            description = 'The id for the second fact' ,
                            rangeTypeName = 'uima.cas.Integer' )
    typesystem.add_feature( type_ = FactRelationship ,
                            name = 'relationship_concept_id' ,
                            description = 'This id for the relationship held between the two facts' ,
                            rangeTypeName = 'uima.cas.Integer' )
    ####
    return( typesystem , NoteNlp )
