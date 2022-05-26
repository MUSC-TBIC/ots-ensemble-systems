
import json

import cassis

import decisionTemplate
from libTypeSystem import loadTypeSystem


identifiedAnnotation_typeString = 'textsem.IdentifiedAnnotation'
eventMention_typeString = 'org.apache.ctakes.typesystem.type.textsem.EventMention'
modifier_typeString = 'org.apache.ctakes.typesystem.type.textsem.Modifier'
timeMention_typeString = 'org.apache.ctakes.typesystem.type.textsem.TimeMention'


def loadCasXmi( cas_xmi_file = 'tests/data/three-classifier-demo.xmi' ):
    typesystem , _ = loadTypeSystem( typesDir = '../types' )
    with open( cas_xmi_file , 'rb' ) as fp:
        cas = cassis.load_cas_from_xmi( fp ,
                                        typesystem = typesystem )
    return( cas )


def loadKB( kb_json_file = 'tests/data/three-classifier-demo-kb.json' ):
    with open( kb_json_file , 'r' ) as fp:
        kb = json.load( fp )
    return( kb )


def test_simple_fill():
    cas = loadCasXmi()
    census = { 'NONE' : 0 }
    decision_profiles = { 'NONE' : 0 }
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
    assert new_decision_profiles == {'NONE': 0, 'Asthma': {}, 'CAD': {}, 'GERD': {}}
    ref_kb = loadKB()
    assert new_kb == ref_kb


def test_fill_with_preexisting_cuis():
    cas = loadCasXmi()
    census = { 'NONE' : 0 , 'Asthma': 5, 'CAD': 2, 'GERD': 3}
    decision_profiles = { 'NONE' : 0 }
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
    assert new_decision_profiles == {'NONE': 0}
    ref_kb = loadKB()
    assert new_kb == ref_kb


def test_seed_kb_with_classifier_1():
    cas = loadCasXmi()
    census = { 'NONE' : 0 }
    decision_profiles = { 'NONE' : 0 }
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
    assert new_decision_profiles == {'NONE': 0}
    ref_kb = loadKB( 'tests/data/three-classifier-demo-kb-classifier-1.json' )
    assert new_kb == ref_kb


def test_seed_kb_with_classifier_2():
    cas = loadCasXmi()
    census = { 'NONE' : 0 }
    decision_profiles = { 'NONE' : 0 }
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
    assert new_decision_profiles == {'NONE': 0}
    ref_kb = loadKB( 'tests/data/three-classifier-demo-kb-classifier-2.json' )
    assert new_kb == ref_kb
    

def test_seed_kb_with_classifier_2():
    cas = loadCasXmi()
    census = { 'NONE' : 0 }
    decision_profiles = { 'NONE' : 0 }
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
    assert new_decision_profiles == {'NONE': 0}
    ref_kb = loadKB( 'tests/data/three-classifier-demo-kb-classifier-2-balanced.json' )
    assert new_kb == ref_kb


def test_seed_kb_with_classifier_3():
    cas = loadCasXmi()
    census = { 'NONE' : 0 }
    decision_profiles = { 'NONE' : 0 }
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
    assert new_decision_profiles == {'NONE': 0}
    ref_kb = loadKB( 'tests/data/three-classifier-demo-kb-classifier-3.json' )
    assert new_kb == ref_kb


##    with open( 'tests/data/kuncheva-eta-2001-table-4-kb-classifier-3.json' , 'w' ) as fp:
##        json.dump( new_kb , fp , indent = 4 )
