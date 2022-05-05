
import json

import libEnsemble


def loadDecisionProfiles( dps_json_file = 'tests/data/three-classifier-demo.json' ):
    with open( dps_json_file , 'r' ) as fp:
        decision_templates = json.load( fp )
    return( decision_templates )

    
def test_cosine_AsthmaAsthmaAsthma():
    decision_templates = loadDecisionProfiles()
    span_profile = json.loads( """{
        "SVM-1" : { 
            "Asthma" : 1 } ,
        "SVM-2" : { 
            "Asthma" : 1 } , 
        "SVM-3" : {
            "Asthma": 1 } 
        }
    """ )
    span_type_cosine = libEnsemble.cosine_profiles( span_profile ,
                                                    decision_templates[ 'Asthma' ] )
    assert round( span_type_cosine , 4 ) == 0.9129


def test_cosine_GERDGERDGERD():
    decision_templates = loadDecisionProfiles()
    span_profile = json.loads( """{
        "SVM-1" : { 
            "GERD" : 1 } ,
        "SVM-2" : { 
            "GERD" : 1 } , 
        "SVM-3" : {
            "GERD": 1 } 
        }
    """ )
    span_type_cosine = libEnsemble.cosine_profiles( span_profile ,
                                                    decision_templates[ 'GERD' ] )
    assert round( span_type_cosine , 4 ) == 1.0


def test_cosine_CADAsthmaAsthma():
    decision_templates = loadDecisionProfiles()
    span_profile = json.loads( """{
        "SVM-1" : { 
            "CAD" : 1 } ,
        "SVM-2" : { 
            "Asthma" : 1 } , 
        "SVM-3" : {
            "Asthma": 1 } 
        }
    """ )
    span_type_cosine = libEnsemble.cosine_profiles( span_profile ,
                                                    decision_templates[ 'Asthma' ] )
    assert round( span_type_cosine , 4 ) == 0.9129

    
def test_cosine_CADNullCAD():
    decision_templates = loadDecisionProfiles()
    span_profile = json.loads( """{
        "SVM-1" : { 
            "CAD" : 1 } ,
        "SVM-3" : {
            "CAD": 1 } 
        }
    """ )
    span_type_cosine = libEnsemble.cosine_profiles( span_profile ,
                                                    decision_templates[ 'CAD' ] )
    assert round( span_type_cosine , 4 ) == 0.8660


def test_cosine_AsthmaNullAsthma():
    decision_templates = loadDecisionProfiles()
    span_profile = json.loads( """{
        "SVM-1" : { 
            "Asthma" : 1 } ,
        "SVM-3" : {
            "Asthma": 1 } 
        }
    """ )
    span_type_cosine = libEnsemble.cosine_profiles( span_profile ,
                                                    decision_templates[ 'GERD' ] )
    assert round( span_type_cosine , 4 ) == 0.0

    
