import argparse
import glob
import os
import re

import logging as log

from tqdm import tqdm

import spacy
import medspacy
import cassis

from math import sqrt

def cosine_profiles( decision_profile ,
                     decision_template ):
    normA = len( decision_profile )
    if( normA == 0 ):
        return( 0.0 )
    normB = 0.0
    dotProduct = 0.0
    for classifier in decision_template:
        if( classifier in decision_profile ):
            for template_type in decision_template[ classifier ]:
                weight = decision_template[ classifier ][ template_type ]
                if( template_type in decision_profile[ classifier ] ):
                    dotProduct += weight
                normB += ( weight ** 2 )
    if( normB == 0 ):
        ##print( '{}\n\n{}'.format( decision_profile ,
        ##                          decision_template ) )
        return( 0.0 )
    cosine_sim = dotProduct / ( sqrt( normA ) * sqrt( normB ) )
    return( cosine_sim )


def cosineSpannedVotes( cas ,
                        NoteNlp ,
                        kb ,
                        decisionProfiles ,
                        classifiers ,
                        votingUnit ,
                        zeroStrategy ):
    ## TODO - add thresholding as a configurable option
    threshold = 0.0
    for span in kb:
        max_cui = 'CUI-less'
        max_cui_sim = 0.0
        ## TODO - allow option to choose CUI based on weighted score
        if( votingUnit == 'sentence' ):
            max_norm_weights = kb[ span ][ 'norm_weights' ][ 'section' ]
        ####
        decision_profile = kb[ span ][ 'decision_profile' ]
        for template_type in decisionProfiles:
            decision_template = decisionProfiles[ template_type ]
            cosine_sim = cosine_profiles( decision_profile ,
                                          decision_template )
            if( cosine_sim > max_cui_sim and
                cosine_sim >= threshold ):
                max_cui = template_type
                max_cui_sim = cosine_sim
        if( zeroStrategy == 'drop' and
            ( ( votingUnit == 'span' and max_cui_sim == 0.0 ) or
              ( votingUnit == 'sentence' and False ) ) ):
            continue
        ## TODO - add special flag to set whether we want to track
        ## CUIs or not
        modifiers = [ 'cosineSimularity={}'.format( max_cui_sim ) ]
        if( votingUnit == 'sentence' ):
            note_nlp = NoteNlp( begin = kb[ span ][ 'begin_offset' ] ,
                                end = kb[ span ][ 'end_offset' ] ,
                                offset = kb[ span ][ 'begin_offset' ] ,
                                nlp_system = 'Decision Template Ensemble System' ,
                                term_modifiers = ';'.join( modifiers ) )
        elif( votingUnit == 'span' ):
            note_nlp = NoteNlp( begin = kb[ span ][ 'begin_offset' ] ,
                                end = kb[ span ][ 'end_offset' ] ,
                                offset = kb[ span ][ 'begin_offset' ] ,
                                nlp_system = 'Decision Template Ensemble System' ,
                                note_nlp_source_concept_id = max_cui ,
                                term_modifiers = ';'.join( modifiers ) )
        cas.add_annotation( note_nlp )
    ####
    return( cas )


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


def cosineDocVotes( cas ,
                    NoteNlp ,
                    kb ,
                    decisionProfiles ,
                    classifiers ,
                    attribute_list ,
                    zeroStrategy ):
    ##print( '{}'.format( decisionProfiles ) )
    ## TODO - add thresholding as a configurable option
    threshold = 0.0
    for concept in kb:
        max_attrib_vals = {}
        max_attrib_sims = {}
        ####
        for attribute in attribute_list:
            decision_profile = kb[ concept ][ attribute ][ 'decision_profile' ]
            for template_type in decisionProfiles[ attribute ]:
                decision_template = decisionProfiles[ attribute ][ template_type ]
                cosine_sim = cosine_profiles( decision_profile ,
                                              decision_template )
                if( attribute not in max_attrib_vals ):
                    max_attrib_vals[ attribute ] = template_type
                    max_attrib_sims[ attribute ] = cosine_sim
                elif( cosine_sim > max_attrib_sims[ attribute ] ):
                    max_attrib_vals[ attribute ] = template_type
                    max_attrib_sims[ attribute ] = cosine_sim
                elif( cosine_sim == max_attrib_sims[ attribute ] ):
                    ## For ties, we want to treat the most extreme or
                    ## noticable value as the preferred value.
                    ## -1 > 1 > 0
                    if( ( int( max_attrib_vals[ attribute ] ) == 0 ) or
                        ( int( max_attrib_vals[ attribute ] ) == 1 and
                          template_type == -1 ) ):
                        max_attrib_vals[ attribute ] = template_type
                        max_attrib_sims[ attribute ] = cosine_sim
            if( zeroStrategy == 'drop' and
                max_attrib_sims[ attribute ] < threshold ):
                continue
        ## TODO - Current scoring can only support a single key/value
        ## pair in the term_modifiers attribute
        ## modifiers = [ 'cosineSimularity={}'.format( max_cui_sim ) ,
        ##              'weighted_confidence={}'.format( int( concept_weight ) / len( classifiers ) ) ]
        modifiers = []
        term_exists = True
        if( 'polarity' in attribute_list ):
            if( int( max_attrib_vals[ 'polarity' ] ) == -1 ):
                term_exists = False
        if( 'uncertainty' in attribute_list ):
            modifiers.append( 'uncertainty={}'.format( int( max_attrib_vals[ 'uncertainty' ] ) ) )
        else:
            modifiers.append( 'uncertainty={}'.format( 0 ) )
        note_nlp = NoteNlp( begin = 0 ,
                            end = 0 ,
                            offset = 0 ,
                            nlp_system = 'Decision Template Ensemble System' ,
                            ## TODO - map this correctly to a CUI
                            note_nlp_source_concept_id = concept ,
                            term_exists = term_exists ,
                            term_modifiers = ';'.join( modifiers ) )
        cas.add_annotation( note_nlp )
    ####
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

