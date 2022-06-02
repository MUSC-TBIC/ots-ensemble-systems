import argparse
import glob
import os
import re

import logging as log

from tqdm import tqdm

import cassis

from libTypeSystem import loadTypeSystem
from libTypeSystem import metadata_typeString, umlsConcept_typeString
from libTypeSystem import eventMention_typeString, modifier_typeString, timeMention_typeString
from libTypeSystem import event_typeString, eventProperties_typeString, attribute_typeString
from libTypeSystem import relationArgument_typeString, binaryTextRelation_typeString

def main( args ):
    teams = [ os.path.basename( f ) for f in glob.glob( os.path.join( args.inputSysDir ,
                                                                      '*' ) ) ]
    for team in sorted( teams ):
        print( '{}'.format( team ) )

    ############################
    typesystem , NoteNlp = loadTypeSystem( typesDir = None , typesFile = args.typesFile )
    FSArray = typesystem.get_type( 'uima.cas.FSArray' )
    noteMetadataType = typesystem.get_type( metadata_typeString )
    eventMentionType = typesystem.get_type( eventMention_typeString )
    modifierType = typesystem.get_type( modifier_typeString )
    timeMentionType = typesystem.get_type( timeMention_typeString )
    eventType = typesystem.get_type( event_typeString )    
    eventPropertiesType = typesystem.get_type( eventProperties_typeString )
    ############################
    ## Iterate over the files
    xmi_filenames = [ os.path.basename( f ) for f in glob.glob( os.path.join( args.inputRefDir ,
                                                                              '*.xmi' ) ) ]
    for xmi_filename in tqdm( xmi_filenames ):
        team_mapping = {}
        with open( os.path.join( args.inputRefDir ,
                                 xmi_filename ) , 'rb' ) as fp:
            cas = cassis.load_cas_from_xmi( fp ,
                                            typesystem = typesystem )
        ########
        team_id = 0
        cas.add_annotation( noteMetadataType( other = '{}={}'.format( 'Oracle' , team_id ) ) )
        team_mapping[ 'Oracle' ] = 0
        for team in sorted( teams ):
            team_id += 1
            team_mapping[ team ] = team_id
            cas.add_annotation( noteMetadataType( other = '{}={}'.format( team , team_id ) ) )
        for eventMention in cas.select( eventMention_typeString ):
            eventMention.__setattr__( "discoveryTechnique" , 0 )
        for modifier in cas.select( modifier_typeString ):
            modifier.__setattr__( "discoveryTechnique" , 0 )
        for timeMention in cas.select( timeMention_typeString ):
            timeMention.__setattr__( "discoveryTechnique" , 0 )
        for team in sorted( teams ):
            with open( os.path.join( args.inputSysDir ,
                                     team ,
                                     xmi_filename ) , 'rb' ) as fp:
                team_cas = cassis.load_cas_from_xmi( fp ,
                                                     typesystem = typesystem )
                team_id = team_mapping[ team ]
                for teamEventMention in team_cas.select( eventMention_typeString ):
                    teamEvent = teamEventMention.get( 'event' )
                    event_cui = teamEvent.get( 'ontologyConcept' )
                    teamEventProperties = teamEvent.get( 'properties' )
                    aspect_val = teamEventProperties.get( 'aspect' )
                    category_val = teamEventProperties.get( 'category' )
                    anEventProperty = eventPropertiesType( aspect = aspect_val ,
                                                           category = category_val )
                    anEvent = eventType( ontologyConcept = event_cui ,
                                         properties = anEventProperty )
                    begin_offset = teamEventMention.get( 'begin' )
                    end_offset = teamEventMention.get( 'end' )
                    ontologyConceptArr = teamEventMention.get( 'ontologyConceptArr' )
                    anEventMention = eventMentionType( begin = begin_offset ,
                                                       end = end_offset ,
                                                       ontologyConceptArr = [ event_cui ] ,
                                                       event = anEvent ,
                                                       discoveryTechnique = team_id )
                    cas.add_annotation( anEventProperty )
                    cas.add_annotation( anEvent )
                    cas.add_annotation( anEventMention )
                modifier_mapping = []
                for relationArg in team_cas.select( relationArgument_typeString ):
                    role_type = relationArg.get( 'role ' )
                    argument = relationArg.get( 'argument' )
                    modifier_mapping[ argument ] = role_type
                for teamModifier in team_cas.select( modifier_typeString ):
                    if( teamModifier.get( 'xmi:id' ) in modifier_mapping ):
                        role_type = modifier_mapping[ teamModifier.get( 'xmi:id' ) ]
                    elif( teamModifier.get( 'category' ) is not None ):
                        role_type = teamModifier.get( 'category' )
                    else:
                        role_type = 'Unknown'
                    aModifier = modifierType( begin = teamModifier.get( 'begin' ) ,
                                              end = teamModifier.get( 'end' ) ,
                                              category = role_type ,
                                              discoveryTechnique = team_id )
                    cas.add_annotation( aModifier )
                for teamTimeMention in team_cas.select( timeMention_typeString ):
                    if( teamTimeMention.get( 'xmi:id' ) in modifier_mapping ):
                        role_type = modifier_mapping[ teamTimeMention.get( 'xmi:id' ) ]
                    elif( teamTimeMention.get( 'timeClass' ) is not None ):
                        role_type = teamTimeMention.get( 'timeClass' )
                    else:
                        role_type = 'Unknown'
                    aTimeMention = timeMentionType( begin = teamTimeMention.get( 'begin' ) ,
                                                    end = teamTimeMention.get( 'end' ) ,
                                                    timeClass = role_type ,
                                                    discoveryTechnique = team_id )
                    cas.add_annotation( aTimeMention )
        ########
        cas.to_xmi( path = os.path.join( args.outputDir ,
                                         xmi_filename ) ,
                    pretty_print = True )

    


if __name__ == '__main__':
    parser = argparse.ArgumentParser( description = 'Simple spaCy pipeline for converting n2c2 2022 social determinants challenge to CAS XMI files with a SHARP-n schema' )
    parser.add_argument( '-v' , '--verbose' ,
                         help = "Log at the DEBUG level" ,
                         action = "store_true" )
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
    
    parser.add_argument( '--types-file' ,
                         required = True ,
                         dest = 'typesFile' ,
                         help = 'XML file containing the types that need to be loaded' )
    
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
