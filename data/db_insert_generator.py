# -*- coding: utf-8 -*-

import os
import sys
import csv
import argparse

from collections import defaultdict

base_path = "../"

utils_path = os.path.join( os.path.dirname( os.path.realpath(__file__) ), base_path + "utils")
sys.path.append( utils_path )

from MyMySQL import MyMySQL



class insertCreator : 
    
    def __init__( self, debug=0 ) : 

        self.debug = debug 
        self._parse_args()

        return 

    def __del__( self ) : 
        pass

    def _parse_args( self ) : 

        parser = argparse.ArgumentParser(description='Will create insert statements so data from EACL21 paper can be added to MySQL' )
        parser.add_argument('--data_location'             , type=str, help='path to input folder', default='./'   )
        parser.add_argument('--output_location'           , type=str, help='path to write to.' , default='./'     )
        parser.add_argument('--language'                  , type=str, help='Language to process.' , default='en'     )

        self.args = parser.parse_args()

        self.data_path_en = os.path.join( self.args.data_location, 'sentences_eacl21', 'en', 'neutral' )
        self.data_path_pt = os.path.join( self.args.data_location, 'sentences_eacl21', 'pt', 'neutral' )

        self.common_strings_en = [ 'This is a ', 'This is an ' ]
        self.common_strings_pt = [ "Este é um ", "Esta é uma ", " ." ]
        
        return

    def get_data( self ) :

        idiomatic_meanings = dict()
        literal_meanings   = dict()
        idioms             = dict()
        for ( lang, path, common_strings ) in [
                ( 'en', self.data_path_en, self.common_strings_en ),
                ( 'pt', self.data_path_pt, self.common_strings_pt ),
                ]: 
            this_idioms = list()
            
            for ( file_name, meaning_type ) in [
                    ( '/P1_sents.csv', idiomatic_meanings ),
                    ( '/P3_sents.csv', literal_meanings ),
                    ] :
                with open( path + file_name ) as csvfile :
                    reader = csv.reader( csvfile )
                    header = True
                    for row in reader :
                        if header :
                            header = False
                            continue
                        this_meaning = row[2]
                        for replacer in common_strings :
                            this_meaning = this_meaning.replace( replacer, '' )
                        this_meaning = this_meaning.lower()
                        this_idiom = row[0].lower()
                        meaning_type[ this_idiom ] = this_meaning
                        if not this_idiom in this_idioms : 
                            this_idioms.append( this_idiom )
                            
            idioms[ lang ] = this_idioms

        self.literal_meanings   = literal_meanings
        self.idiomatic_meanings = idiomatic_meanings
        self.idioms = idioms
        return
                

    def write_idioms_insert( self ) :

        querys = list()
        for language in ( 'en', 'pt' ) :
            for idiom in self.idioms[ language ] :
                query = 'insert into idioms( idiom, language ) values ( "' + idiom + '", "' + language + '" );'
                querys.append( query )

        outfile = os.path.join( self.args.output_location, 'idiom_insert.sql' )
        with open( outfile, 'w' ) as fh :
            for query in querys :
                fh.write( query )
                fh.write( "\n" )
        print( "Wrote" ,  outfile )


    def write_meanings_insert( self ) :

        querys = list()
        mysql_obj = MyMySQL( config_path = utils_path )
        idioms = mysql_obj.mysql_get( "select * from idioms" )
        for idiom in reversed( idioms ) :
            this_id    = int( idiom[0] )
            this_lang  = idiom[2]
            this_idiom = idiom[1].encode("utf-8")
            
            meanings   = [ self.literal_meanings[ this_idiom ], self.idiomatic_meanings[ this_idiom ] ]
            if this_lang == 'en' :
                meanings.append( 'Other')
            elif this_lang == 'pt' :
                meanings.append( 'Outro (other)')
                
            for this_meaning in meanings :
                this_query = "insert into meanings( idiom_id, meaning ) values( " + str( this_id ) + ', "' + this_meaning + '" );'
                querys.append( this_query )
                    
        outfile = os.path.join( self.args.output_location, 'meaning_insert.sql' )
        
        with open( outfile, 'w' ) as fh :
            for query in querys :
                fh.write( query )
                fh.write( "\n" )
        print( "Wrote", outfile ) 

    def write_out_meanings( self, language=None ) :
        
        mysql_obj = MyMySQL( config_path = utils_path )
        query     = "SELECT * FROM idioms"
        if not language is None :
            query += " where language='" + language + "';"
        idioms = mysql_obj.mysql_get( query ) 
        for idiom in reversed( idioms ) :
            this_id    = int( idiom[0] )
            this_lang  = idiom[2]
            this_idiom = idiom[1]
            
            meanings   = [ self.literal_meanings[ this_idiom ], self.idiomatic_meanings[ this_idiom ] ]
            print( this_idiom + ", " + meanings[0] + "," + meanings[1] )


if __name__ == '__main__' :

    ic = insertCreator()
    ic.get_data()

    ## Run write_idioms_insert, write result to database before running write_meanings_insert
    # ic.write_idioms_insert()
    # ic.write_meanings_insert()

    ## This will list idioms and meanings in CSV.
    ic.write_out_meanings( 'en' )

