
import pytest

import os
import json

import cassis

import decisionTemplate
from libTypeSystem import loadTypeSystem
from libTypeSystem import umlsConcept_typeString
from libTypeSystem import identifiedAnnotation_typeString, eventMention_typeString


def loadCasXmi( cas_xmi_file = 'tests/data/three-classifier-demo.xmi' ,
                typesFile = None ):
    if( typesFile is None ):
        typesystem , _ = loadTypeSystem( typesDir = '../types' )
    else:
        typesystem , _ = loadTypeSystem( typesDir = None ,
                                         typesFile = typesFile )
    ########
    with open( cas_xmi_file , 'rb' ) as fp:
        cas = cassis.load_cas_from_xmi( fp ,
                                        typesystem = typesystem )
    return( cas )


def loadJSON( json_file = 'tests/data/three-classifier-demo-kb.json' ):
    with open( json_file , 'r' ) as fp:
        json_data = json.load( fp )
    return( json_data )


def saveJSON( json_data , json_file ):
    with open( json_file , 'w' ) as fp:
        json.dump( json_data , fp , indent = 4 )


def test_load_asthma_cui_map():
    cas = loadCasXmi()
    xmiId2cui = decisionTemplate.extractCuiMap( cas )
    assert xmiId2cui == { 10 : "Asthma" ,
                          11 : "CAD" ,
                          12 : "GERD" }


@pytest.mark.filterwarnings("ignore:Feature")
def test_load_sdoh_cui_map():
    if( not os.path.exists( '/Users/pmh/bin/apache-ctakes-4.0.0.1/resources/org/apache/ctakes/typesystem/types/TypeSystem.xml' ) ):
        pytest.skip( 'Skipping because full SHARPn type system file not found' )
    ########
    cas = loadCasXmi( cas_xmi_file = 'tests/data/sharpn-ref/living-and-smoking.xmi' ,
                      typesFile = '/Users/pmh/bin/apache-ctakes-4.0.0.1/resources/org/apache/ctakes/typesystem/types/TypeSystem.xml' )
    xmiId2cui = decisionTemplate.extractCuiMap( cas )
    assert xmiId2cui == { 2  : 'C2184149' ,
                          3  : 'C0439044' ,
                          4  : 'C0557130' ,
                          5  : 'C3242657' ,
                          6  : 'C0237154' ,
                          7  : 'C0242271' ,
                          8  : 'C0557351' ,
                          9  : 'C0041674' ,
                          10 : "C0035345" ,
                          11 : "C0682148" ,
                          12 : "C0038492" ,
                          13 : 'C0555052' ,
                          14 : 'C0001948' ,
                          15 : 'C0281875' ,
                          16 : 'C1287520' ,
                          17 : 'C1971295' ,
                          18 : 'C1698618' ,
                          19 : 'C3853727' }
    

def test_simple_fill():
    cas = loadCasXmi()
    census = { 'NONE' : 0 }
    decision_profiles = { 'NONE' : {} }
    orig_kb = {}
    xmiId2cui = { 10 : "Asthma" ,
                  11 : "CAD" ,
                  12 : "GERD" }
    new_census , new_decision_profiles , new_kb = decisionTemplate.seedSpansInKb( cas ,
                                                                                  census ,
                                                                                  decision_profiles ,
                                                                                  orig_kb ,
                                                                                  xmiId2cui ,
                                                                                  identifiedAnnotation_typeString ,
                                                                                  trainPhase = True ,
                                                                                  top_classifier_id = '1' ,
                                                                                  weighting = 'ranked' )
    assert new_census == {'NONE': 0, 'Asthma': 0, 'CAD': 0, 'GERD': 0}
    assert new_decision_profiles == {'NONE': {}, 'Asthma': {}, 'CAD': {}, 'GERD': {}}
    ref_kb = loadJSON()
    assert new_kb == ref_kb


def test_fill_with_preexisting_cuis():
    cas = loadCasXmi()
    census = { 'NONE' : 0 , 'Asthma': 5, 'CAD': 2, 'GERD': 3}
    decision_profiles = { 'NONE' : {} }
    orig_kb = {}
    xmiId2cui = { 10 : "Asthma" ,
                  11 : "CAD" ,
                  12 : "GERD" }
    new_census , new_decision_profiles , new_kb = decisionTemplate.seedSpansInKb( cas ,
                                                                                  census ,
                                                                                  decision_profiles ,
                                                                                  orig_kb ,
                                                                                  xmiId2cui ,
                                                                                  identifiedAnnotation_typeString ,
                                                                                  trainPhase = True ,
                                                                                  top_classifier_id = '1' ,
                                                                                  weighting = 'ranked' )
    assert new_census == {'NONE': 0 , 'Asthma': 5, 'CAD': 2, 'GERD': 3}
    assert new_decision_profiles == {'NONE': {}}
    ref_kb = loadJSON()
    assert new_kb == ref_kb


def test_seed_kb_with_classifier_1():
    cas = loadCasXmi()
    census = { 'NONE' : 0 }
    decision_profiles = { 'NONE' : {} }
    orig_kb = {}
    xmiId2cui = { 10 : "Asthma" ,
                  11 : "CAD" ,
                  12 : "GERD" }
    new_census , new_decision_profiles , new_kb = decisionTemplate.seedSpansInKb( cas ,
                                                                                  census ,
                                                                                  decision_profiles ,
                                                                                  orig_kb ,
                                                                                  xmiId2cui ,
                                                                                  identifiedAnnotation_typeString ,
                                                                                  trainPhase = False ,
                                                                                  top_classifier_id = '1' ,
                                                                                  weighting = 'ranked' )
    assert new_census == {'NONE': 0}
    assert new_decision_profiles == {'NONE': {}}
    ref_kb = loadJSON( 'tests/data/three-classifier-demo-kb-classifier-1.json' )
    assert new_kb == ref_kb


def test_seed_kb_with_classifier_2():
    cas = loadCasXmi()
    census = { 'NONE' : 0 }
    decision_profiles = { 'NONE' : {} }
    orig_kb = {}
    xmiId2cui = { 10 : "Asthma" ,
                  11 : "CAD" ,
                  12 : "GERD" }
    new_census , new_decision_profiles , new_kb = decisionTemplate.seedSpansInKb( cas ,
                                                                                  census ,
                                                                                  decision_profiles ,
                                                                                  orig_kb ,
                                                                                  xmiId2cui ,
                                                                                  identifiedAnnotation_typeString ,
                                                                                  trainPhase = False ,
                                                                                  top_classifier_id = '2' ,
                                                                                  weighting = 'ranked' )
    assert new_census == {'NONE': 0}
    assert new_decision_profiles == {'NONE': {}}
    ref_kb = loadJSON( 'tests/data/three-classifier-demo-kb-classifier-2.json' )
    assert new_kb == ref_kb
    

def test_seed_kb_with_classifier_2():
    cas = loadCasXmi()
    census = { 'NONE' : 0 }
    decision_profiles = { 'NONE' : {} }
    orig_kb = {}
    xmiId2cui = { 10 : "Asthma" ,
                  11 : "CAD" ,
                  12 : "GERD" }
    new_census , new_decision_profiles , new_kb = decisionTemplate.seedSpansInKb( cas ,
                                                                                  census ,
                                                                                  decision_profiles ,
                                                                                  orig_kb ,
                                                                                  xmiId2cui ,
                                                                                  identifiedAnnotation_typeString ,
                                                                                  trainPhase = False ,
                                                                                  top_classifier_id = '2' ,
                                                                                  weighting = 'balanced' )
    assert new_census == {'NONE': 0}
    assert new_decision_profiles == {'NONE': {}}
    ref_kb = loadJSON( 'tests/data/three-classifier-demo-kb-classifier-2-balanced.json' )
    assert new_kb == ref_kb


def test_seed_kb_with_classifier_3():
    cas = loadCasXmi()
    census = { 'NONE' : 0 }
    decision_profiles = { 'NONE' : {} }
    orig_kb = {}
    xmiId2cui = { 10 : "Asthma" ,
                  11 : "CAD" ,
                  12 : "GERD" }
    new_census , new_decision_profiles , new_kb = decisionTemplate.seedSpansInKb( cas ,
                                                                                  census ,
                                                                                  decision_profiles ,
                                                                                  orig_kb ,
                                                                                  xmiId2cui ,
                                                                                  identifiedAnnotation_typeString ,
                                                                                  trainPhase = False ,
                                                                                  top_classifier_id = '3' ,
                                                                                  weighting = 'ranked' )
    assert new_census == {'NONE': 0}
    assert new_decision_profiles == {'NONE': {}}
    ref_kb = loadJSON( 'tests/data/three-classifier-demo-kb-classifier-3.json' )
    assert new_kb == ref_kb


def test_simple_process_annots():
    cas = loadCasXmi()
    census = { 'NONE' : 0 }
    decision_profiles = { 'NONE' : {} }
    kb = {}
    xmiId2cui = { 10 : "Asthma" ,
                  11 : "CAD" ,
                  12 : "GERD" }
    census , decision_profiles , kb = decisionTemplate.seedSpansInKb( cas ,
                                                                      census ,
                                                                      decision_profiles ,
                                                                      kb ,
                                                                      xmiId2cui ,
                                                                      identifiedAnnotation_typeString ,
                                                                      trainPhase = True ,
                                                                      top_classifier_id = '1' ,
                                                                      weighting = 'ranked' )
    census , decision_profiles , kb = decisionTemplate.processRemainingAnnotations( cas ,
                                                                                    'unitTest.xmi' ,
                                                                                    census ,
                                                                                    decision_profiles ,
                                                                                    kb ,
                                                                                    xmiId2cui ,
                                                                                    identifiedAnnotation_typeString ,
                                                                                    trainPhase = True ,
                                                                                    classifiers = [ '1' , '2' , '3' ] ,
                                                                                    top_classifier_id = '1' ,
                                                                                    votingUnit = 'span' ,
                                                                                    weighting = 'ranked' ,
                                                                                    partialMatchWeight = 1.0 )
    ref_census = loadJSON( 'tests/data/three-classifier-demo-census-classifier-1.json' )
    assert census == ref_census
    ref_decision_profiles = loadJSON( 'tests/data/three-classifier-demo-dp-classifier-1.json' )
    assert decision_profiles == ref_decision_profiles
    ref_kb = loadJSON( 'tests/data/three-classifier-demo-kbAll-classifier-1.json' )
    assert kb == ref_kb

    
def test_simple_process_annots_balanced():
    cas = loadCasXmi()
    census = { 'NONE' : 0 }
    decision_profiles = { 'NONE' : {} }
    kb = {}
    xmiId2cui = { 10 : "Asthma" ,
                  11 : "CAD" ,
                  12 : "GERD" }
    census , decision_profiles , kb = decisionTemplate.seedSpansInKb( cas ,
                                                                      census ,
                                                                      decision_profiles ,
                                                                      kb ,
                                                                      xmiId2cui ,
                                                                      identifiedAnnotation_typeString ,
                                                                      trainPhase = True ,
                                                                      top_classifier_id = '1' ,
                                                                      weighting = 'balanced' )
    census , decision_profiles , kb = decisionTemplate.processRemainingAnnotations( cas ,
                                                                                    'unitTest.xmi' ,
                                                                                    census ,
                                                                                    decision_profiles ,
                                                                                    kb ,
                                                                                    xmiId2cui ,
                                                                                    identifiedAnnotation_typeString ,
                                                                                    trainPhase = True ,
                                                                                    classifiers = [ '1' , '2' , '3' ] ,
                                                                                    top_classifier_id = '1' ,
                                                                                    votingUnit = 'span' ,
                                                                                    weighting = 'balanced' ,
                                                                                    partialMatchWeight = 1.0 )
    assert census == {'NONE': 1, 'Asthma': 5, 'CAD': 4, 'GERD': 4}
    ref_decision_profiles = loadJSON( 'tests/data/three-classifier-demo-dp-classifier-1-balanced.json' )
    assert decision_profiles == ref_decision_profiles
    ref_kb = loadJSON( 'tests/data/three-classifier-demo-kbAll-classifier-1-balanced.json' )
    assert kb == ref_kb

    
def test_process_annots_for_run():
    cas = loadCasXmi()
    census = loadJSON( 'tests/data/three-classifier-demo-census-classifier-1.json' )
    decision_profiles = loadJSON( 'tests/data/three-classifier-demo-dp-classifier-1.json' )
    kb = {}
    xmiId2cui = { 10 : "Asthma" ,
                  11 : "CAD" ,
                  12 : "GERD" }
    census , decision_profiles , kb = decisionTemplate.seedSpansInKb( cas ,
                                                                      census ,
                                                                      decision_profiles ,
                                                                      kb ,
                                                                      xmiId2cui ,
                                                                      identifiedAnnotation_typeString ,
                                                                      trainPhase = False ,
                                                                      top_classifier_id = '1' ,
                                                                      weighting = 'ranked' )
    census , decision_profiles , kb = decisionTemplate.processRemainingAnnotations( cas ,
                                                                                    'unitTest.xmi' ,
                                                                                    census ,
                                                                                    decision_profiles ,
                                                                                    kb ,
                                                                                    xmiId2cui ,
                                                                                    identifiedAnnotation_typeString ,
                                                                                    trainPhase = False ,
                                                                                    classifiers = [ '1' , '2' , '3' ] ,
                                                                                    top_classifier_id = '1' ,
                                                                                    votingUnit = 'span' ,
                                                                                    weighting = 'ranked' ,
                                                                                    partialMatchWeight = 1.0 )
    ref_census = loadJSON( 'tests/data/three-classifier-demo-census-classifier-1.json' )
    assert census == ref_census
    ref_decision_profiles = loadJSON( 'tests/data/three-classifier-demo-dp-classifier-1.json' )
    assert decision_profiles == ref_decision_profiles
    ref_kb = loadJSON( 'tests/data/three-classifier-demo-kbRun-classifier-1.json' )
    assert kb == ref_kb


def test_process_annots_for_partial_run():
    cas = loadCasXmi()
    census = loadJSON( 'tests/data/three-classifier-demo-census-classifier-1.json' )
    decision_profiles = loadJSON( 'tests/data/three-classifier-demo-dp-classifier-1.json' )
    kb = {}
    xmiId2cui = { 10 : "Asthma" ,
                  11 : "CAD" ,
                  12 : "GERD" }
    census , decision_profiles , kb = decisionTemplate.seedSpansInKb( cas ,
                                                                      census ,
                                                                      decision_profiles ,
                                                                      kb ,
                                                                      xmiId2cui ,
                                                                      identifiedAnnotation_typeString ,
                                                                      trainPhase = False ,
                                                                      top_classifier_id = '1' ,
                                                                      weighting = 'ranked' )
    census , decision_profiles , kb = decisionTemplate.processRemainingAnnotations( cas ,
                                                                                    'unitTest.xmi' ,
                                                                                    census ,
                                                                                    decision_profiles ,
                                                                                    kb ,
                                                                                    xmiId2cui ,
                                                                                    identifiedAnnotation_typeString ,
                                                                                    trainPhase = False ,
                                                                                    classifiers = [ '1' , '2' ] ,
                                                                                    top_classifier_id = '1' ,
                                                                                    votingUnit = 'span' ,
                                                                                    weighting = 'ranked' ,
                                                                                    partialMatchWeight = 1.0 )
    ref_census = loadJSON( 'tests/data/three-classifier-demo-census-classifier-1.json' )
    assert census == ref_census
    ref_decision_profiles = loadJSON( 'tests/data/three-classifier-demo-dp-classifier-1-no-3.json' )
    assert decision_profiles == ref_decision_profiles
    ref_kb = loadJSON( 'tests/data/three-classifier-demo-kbRun-classifier-1-no-3.json' )
    assert kb == ref_kb



def test_process_annots_for_partial_weights_run():
    cas = loadCasXmi()
    census = loadJSON( 'tests/data/three-classifier-demo-census-classifier-1.json' )
    decision_profiles = loadJSON( 'tests/data/three-classifier-demo-dp-classifier-1.json' )
    kb = {}
    xmiId2cui = { 10 : "Asthma" ,
                  11 : "CAD" ,
                  12 : "GERD" }
    census , decision_profiles , kb = decisionTemplate.seedSpansInKb( cas ,
                                                                      census ,
                                                                      decision_profiles ,
                                                                      kb ,
                                                                      xmiId2cui ,
                                                                      identifiedAnnotation_typeString ,
                                                                      trainPhase = False ,
                                                                      top_classifier_id = '1' ,
                                                                      weighting = 'ranked' )
    census , decision_profiles , kb = decisionTemplate.processRemainingAnnotations( cas ,
                                                                                    'unitTest.xmi' ,
                                                                                    census ,
                                                                                    decision_profiles ,
                                                                                    kb ,
                                                                                    xmiId2cui ,
                                                                                    identifiedAnnotation_typeString ,
                                                                                    trainPhase = False ,
                                                                                    classifiers = [ '1' , '2' , '3' ] ,
                                                                                    top_classifier_id = '1' ,
                                                                                    votingUnit = 'span' ,
                                                                                    weighting = 'ranked' ,
                                                                                    partialMatchWeight = 0.5 )
    ref_census = loadJSON( 'tests/data/three-classifier-demo-census-classifier-1.json' )
    assert census == ref_census
    ref_decision_profiles = loadJSON( 'tests/data/three-classifier-demo-dp-classifier-1-partial-weight.json' )
    assert decision_profiles == ref_decision_profiles
    ref_kb = loadJSON( 'tests/data/three-classifier-demo-kbRun-classifier-1-partial-weight.json' )
    assert kb == ref_kb


@pytest.mark.filterwarnings("ignore:Feature")
def test_simple_fill_with_event_mentions():
    if( not os.path.exists( '/Users/pmh/bin/apache-ctakes-4.0.0.1/resources/org/apache/ctakes/typesystem/types/TypeSystem.xml' ) ):
        pytest.skip( 'Skipping because full SHARPn type system file not found' )
    ########
    cas = loadCasXmi( cas_xmi_file = 'tests/data/sharpn-out/living-and-smoking.xmi' ,
                      typesFile = '/Users/pmh/bin/apache-ctakes-4.0.0.1/resources/org/apache/ctakes/typesystem/types/TypeSystem.xml' )
    xmiId2cui = decisionTemplate.extractCuiMap( cas )
    census = { 'NONE' : 0 }
    decision_profiles = { 'NONE' : {} }
    kb = {}
    census , decision_profiles , kb = decisionTemplate.seedSpansInKb( cas ,
                                                                      census ,
                                                                      decision_profiles ,
                                                                      kb ,
                                                                      xmiId2cui ,
                                                                      eventMention_typeString ,
                                                                      trainPhase = True ,
                                                                      top_classifier_id = '1' ,
                                                                      weighting = 'ranked' )
    assert census == { "NONE": 0,
                       "C2184149": 0,
                       "C1287520": 0
                      }
    assert decision_profiles == { "NONE": {},
                                  "C2184149": {},
                                  "C1287520": {}
                                 }


@pytest.mark.filterwarnings("ignore:Feature")
def test_simple_run_with_event_mentions():
    if( not os.path.exists( '/Users/pmh/bin/apache-ctakes-4.0.0.1/resources/org/apache/ctakes/typesystem/types/TypeSystem.xml' ) ):
        pytest.skip( 'Skipping because full SHARPn type system file not found' )
    ########
    cas = loadCasXmi( cas_xmi_file = 'tests/data/sharpn-out/living-and-smoking.xmi' ,
                      typesFile = '/Users/pmh/bin/apache-ctakes-4.0.0.1/resources/org/apache/ctakes/typesystem/types/TypeSystem.xml' )
    xmiId2cui = decisionTemplate.extractCuiMap( cas )
    census = { 'NONE' : 0 }
    decision_profiles = { 'NONE' : {} }
    kb = {}
    census , decision_profiles , kb = decisionTemplate.seedSpansInKb( cas ,
                                                                      census ,
                                                                      decision_profiles ,
                                                                      kb ,
                                                                      xmiId2cui ,
                                                                      eventMention_typeString ,
                                                                      trainPhase = True ,
                                                                      top_classifier_id = '1' ,
                                                                      weighting = 'ranked' )
    census , decision_profiles , kb = decisionTemplate.processRemainingAnnotations( cas ,
                                                                                    'living-and-smoking.xmi' ,
                                                                                    census ,
                                                                                    decision_profiles ,
                                                                                    kb ,
                                                                                    xmiId2cui ,
                                                                                    eventMention_typeString ,
                                                                                    trainPhase = True ,
                                                                                    classifiers = [ '1' , '2' ] ,
                                                                                    top_classifier_id = '1' ,
                                                                                    votingUnit = 'span' ,
                                                                                    weighting = 'ranked' ,
                                                                                    partialMatchWeight = 1.0 )
    assert census == { "NONE": 0,
                       "C2184149": 1 ,
                       "C1287520": 2
                      }
    ref_decision_profiles = loadJSON( 'tests/data/sharpn-out/decision_profiles.json' )
    assert decision_profiles == ref_decision_profiles
    ref_kb = loadJSON( 'tests/data/sharpn-out/kb.json' )
    assert kb == ref_kb
