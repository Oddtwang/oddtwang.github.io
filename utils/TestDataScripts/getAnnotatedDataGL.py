import re
import os
import csv
import sys
import json
import time
import spacy
import pickle
import unidecode

base_path  = '../../'
utils_path = os.path.join( os.path.dirname( os.path.realpath(__file__) ), base_path + "utils")
sys.path.append( utils_path )

from MyMySQL                import MyMySQL
mysql_obj = MyMySQL(config_path=utils_path)

import random
random.seed( 52 ) 

idioms_first_two_meanings = dict()


def get_data( language, table ) : 

    ## In GL, things are a lot more straight forward. No new meanings.


    new_meanings = {
        'banda ancha' : {
            'internet de alta velocidade' : 'internet rápida',
        },
        'fenda dixital' : {
            'diferenza de acceso ás novas tecnoloxías' : 'diferenza de acceso a internet',
        },
        'memoria viva' : {
            'personalidade relevante que aínda vive' : 'personalidade relevante viva' ,
        },
        'monte baixo' : {
            'monte con arbustos pequenos' : 'monte con arbustos' ,
        },
        'paseo marítimo' : {
            'camiño construído á beira do mar' : 'camiño construído à beiramar',
        },
        'pegada ecolóxica' : {
            'indicador de sustentabilidade das actividades humanas' : 'indicador de sustentabilidade',
        },
        'tempo parcial' : {
            'compatibilización entre varias tarefas' : 'compatibilización entre tarefas',
        },
        'venres negro' : {
            'descontos na compra online' : 'descontos online',
        },
        'vida laboral' : {
            'parte da vida dedicada ao traballo' : 'tempo dedicado ao traballo',
            'informe do traballos realizados' : 'informe de traballos realizados' ,
        },
    }

    
    query   = "SELECT idiom_id, idiom FROM idioms WHERE language = '" + language + "';"
    results = list( reversed( mysql_obj.mysql_get( query ) ) )

    meaning_edit = list()
    idiom_data   = list()
    added_sents  = list()
    for idiom_id, idiom in results :

        query    = "SELECT meaning_id, idiom_id, meaning FROM meanings WHERE idiom_id = " + str( idiom_id ) + " ORDER BY meaning_id DESC;"
        meanings = list( mysql_obj.mysql_get( query ) ) 

        results  = None
        if table == 'annotations_p3' : 
            query    = "SELECT data FROM annotations_p3 WHERE idiom_id = " + str( idiom_id ) + " order by annotation_id DESC limit 1;"
            results  = list( reversed( mysql_obj.mysql_get( query ) ) )
            if len( results ) == 0 :
                raise Exception( "Did not find meanings!" ) 
        else :
            print( "WARNING: Picking from non-final table. Use this only for kappa calculation" )
            query    = "SELECT data FROM " + table + " WHERE idiom_id = " + str( idiom_id ) + " order by annotation_id DESC limit 1;"
            print( "Query: {}".format( query ) ) 
            time.sleep( 2 )
            results  = list( reversed( mysql_obj.mysql_get( query ) ) )
            
            

        best_result = ''
        for result in results : 
            result = result[0]
            result = re.sub( r'^\'', '', result )
            result = re.sub( r'\'$', '', result )
            if len( result ) > len( best_result ) :
                best_result = result

        annotations = None
        try : 
            annotations = json.loads( best_result )
        except :
            print( "JSON load fail debug", file=sys.stderr )
            import pdb; pdb.set_trace()

        labels        = annotations[ 'annotations' ]
        ann_meanings  = annotations[ 'meanings'    ]
        ann_sentences = annotations[ 'sentences'   ]

        ## label_meaning_changes = dict()

        ## ann_meanings and meanings should have the correct two in order
        ann_meanings_actual = [ i[-1] for i in ann_meanings ]
        meanings_actual     = [ i[-1] for i in meanings ]
        assert meanings_actual[ :2 ] == ann_meanings_actual[ :2 ]


        idioms_first_two_meanings[ idiom ] = meanings_actual[:2]

        ## validate labels
        meanings_dict    = dict()
        id_meanings_dict = dict()
        for this_meaning_id, this_idiom_id, this_meaning in meanings :
            assert this_idiom_id == idiom_id
            if this_meaning == 'Outro (other)' :
                this_meaning = 'Discard'
            meanings_dict[ this_meaning_id ] = this_meaning
            id_meanings_dict[ this_meaning ] = this_meaning_id

        discard_debug = False
        for this_meaning_id, this_meaning in ann_meanings :
            if this_meaning_id == 0 and this_meaning == 'Discard' :
                discard_debug = True
                continue
            try :
                assert meanings_dict[ this_meaning_id ] == this_meaning
            except KeyError :
                print( "Meaning mismatch debug", file=sys.stderr )
                import pdb; pdb.set_trace()

        # if discard_debug :
        #     import pdb; pdb.set_trace()

        ## End of validation

        ## Meanings, None, Proper Noun, Meta Usage --> This is how we want everything listed with first meaning being literal
        meanings  = list()
        meanings += [ i for i in ann_meanings if not i[1] in ['Proper Noun', 'Meta Usage', 'Discard'] ]
        meanings += [[ 0, 'None'] ] * ( 4 - len( meanings ) )
        meanings += [ i for i in ann_meanings if i[1] in [ 'Proper Noun', 'Meta Usage' ] ]

        assert all( [ ( i[1] != 'Discard' ) for i in meanings ] )

        meaning_len = 6
        if len( meanings ) != meaning_len :
            print( "Failed meaning len assert" )
            import pdb; pdb.set_trace()
        assert len( meanings ) == meaning_len


        idiom_rows  = list()
        for index in range( len( labels ) ) :

            this_sent_row = [ idiom_id, idiom ] + [ i[1] for i in meanings ]

            label_meaning = None
            for meaning in ann_meanings :
                if int( labels[ index ] ) == int( meaning[0] ) :
                    label_meaning = meaning[1]


            if label_meaning == 'Discard' :
                continue

            # if is_only_literal :
            #     if label_meaning in idioms_first_two_meanings[ idiom ] :
            #         correct_literal_meaning = idioms_first_two_meanings[ idiom ][1]
            #         if label_meaning != correct_literal_meaning :
            #             ## print( "Updating label meaning to {} for only literal idiom {}".format( correct_literal_meaning, idiom ) )
            #             label_meaning = correct_literal_meaning


            # ## Fix if we changed the meaning of a literal only after annotation -- this is required because updating "ann_meanings" will not take care of this.
            # if label_meaning in label_meaning_changes.keys() :
            #     label_meaning = label_meaning_changes[ label_meaning ]


                
            is_literal    = None
            if meanings[0][1] == label_meaning or label_meaning == 'Proper Noun' :
                is_literal = 1
            else :
                is_literal = 0
                
            assert not label_meaning is None
            assert not is_literal    is None
            ## Note that we are using meanings from ann_meanings
            assert label_meaning in [ i[1] for i in meanings ] 
            
            this_sent_row.append( is_literal    )
            this_sent_row.append( label_meaning )


            if not all( [ ( len( i ) > 0 ) for i in ann_sentences[ index ][ 'data' ] ] ) :
                print( "Skipping entry because all three sentences are not present..." ) 
                continue
            
            this_sent_row += ann_sentences[ index ][ 'data' ]
                
            required_len = 14
            if len( this_sent_row ) != required_len :
                print( this_sent_row, len( this_sent_row ) )
                sys.exit()

            assert len( this_sent_row ) == required_len

            this_entry = ann_sentences[ index ][ 'data' ][1].lower()

            ## Postprocessing
            ## 1. Make sure that the shortened meanings are used here.
            ##    1.1. This must be used for both the possible meaning and annotation (if it is that meaning)
            ## 2. Make sure that sentences that contain the idiom twice are dropped
            ## 3. Make sure that sentences where the idiom is an inflection are dropped.

            if idiom in new_meanings.keys() :
                found_one = False
                for index in [ 2, 3, 4, 5, 9 ] : # 6, 7 are proper noun and meta, 8 is bool for not idiomatic.
                    if this_sent_row[ index ] in new_meanings[ idiom ] :
                        found_one = True
                        this_sent_row[ index ] = new_meanings[ idiom ][ this_sent_row[ index ] ]
                assert found_one
                meaning_edit.append( idiom ) 
                

            ## Count how many times we have idiom in target
            count = len( re.findall(r'' + this_sent_row[1].lower(), this_sent_row[11].lower() ) ) 
            if count > 1 :
                print( "Skipping {}, contains {} more than once".format( this_sent_row[11], this_sent_row[1] ) )
                continue
            assert count == 1

            ## Drop sentences where idiom is inflected.
            if not this_sent_row[1].lower() in this_sent_row[11].lower() :
                print( "Skipping {}, does not caontain idiom {}!".format( this_sent_row[11], this_sent_row[1] ) )
                continue
            if this_sent_row[1].lower() + 's' in this_sent_row[11].lower() :
                print( "Skipping {}, contains inflection of idiom {}!".format( this_sent_row[11], this_sent_row[1] ) )
                continue


            ## Post processing complete.


            if this_entry in added_sents :
                print( "Repeat sentence, ignoring ... " ) 
                continue
            else : 
                added_sents.append( this_entry )
            idiom_rows.append( this_sent_row )

        idiom_data.append( idiom_rows )


    return idiom_data


def _load_compositionality( language ) :
    idiom_compositionality = dict()
    location = '../data/' + language + '.filtered.csv' 
    with open( location ) as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        relevant_indexes = None
        for row in reader:
            if relevant_indexes is None :
                relevant_indexes = [ row.index( 'compound_surface' ), row.index( 'compositionality' ) ]
                continue
            this_idiom       = ' '.join( row[ relevant_indexes[ 0 ] ].split( '_' ) ).lower()
            compositionality = float( row[ relevant_indexes[ 1 ] ] )
            idiom_compositionality[ this_idiom ] = compositionality
    return idiom_compositionality


def split_idiom_data( idiom_data, compositionality, language ) :


    ## Now remove from test and dev elements for training.
    train_from_test_dev = [ list() ]
    new_test_dev        = [ list() ]
    for index in range( 1 ) :
        process_data = [ idiom_data ]
        this_move    = 0
        this_keep    = 0
        
        for idiom_index in range( len( process_data[ index ] ) ) :
            idiom       = process_data[ index ][ idiom_index ]
            idiom_sents = len(idiom) 
            meanings    = list( set( idiom[0][2:8] ) )
            try :
                meanings.remove( 'None' )
            except ValueError :
                pass
            meanings_dict = dict()
            for meaning in meanings :
                meanings_dict[ meaning ] = list()
            for sent in idiom :
                meanings_dict[ sent[9] ].append( sent )

            move_to_train = list()


            meanings_list = list( meanings_dict.keys() )
            for elem in ['Proper Noun', 'Meta Usage' ] :
                meanings_list.remove( elem )
            meanings_list = meanings_list + ['Proper Noun', 'Meta Usage' ] ## Make sure this is at the END (we pick from here if we can't find others)

            need = [ 0, 1 ]
            counts = { 0 : 0, 1 : 0 }
            for meaning in meanings_list : 
                for sent in meanings_dict[ meaning ] :
                    counts[ sent[ 8 ] ] += 1

            new_need = list()
            for label in need :
                if counts[ label ] > 1 :
                    new_need.append( label )
            need = new_need
            move_to_train = list()
            
            this_idiom_sents       = list()
            this_idiom_sents_train = list()
            for meaning in meanings_list : 
                for sent in meanings_dict[ meaning ] :
                    if sent[ 8 ] in need : 
                        this_idiom_sents_train.append( sent )
                        need.remove( sent[ 8 ] )
                    else :
                        this_idiom_sents.append( sent ) 
                    
            this_keep_here = this_idiom_sents
            move_to_train  = this_idiom_sents_train
            assert idiom_sents == ( len( this_keep_here ) + len( move_to_train ) )
            assert len( this_keep_here ) > 0

            train_from_test_dev[ index ].append( move_to_train )
            new_test_dev[ index ].append( this_keep_here )


            
            # for meaning in meanings :
            #     examples_of_this_meaning = len( meanings_dict[ meaning ] )
            #     to_train_count           = int( 0.25 *  len( meanings_dict[ meaning ] ) )
            #     if to_train_count == 0 and examples_of_this_meaning > 1 :
            #         to_train_count = 1
            #     move_to_train += meanings_dict[ meaning ][ : to_train_count ] 
            #     meanings_dict[ meaning ] = meanings_dict[ meaning ][ to_train_count : ]

            # this_keep_here = list()
            # for meaning in meanings_dict.keys() :
            #     this_keep_here += meanings_dict[ meaning ]

            # assert idiom_sents == ( len( this_keep_here ) + len( move_to_train ) )
            # if idiom_sents == 0 :
            #     print( "No sents", idiom[0][1] )
            #     continue
            # assert len( this_keep_here ) > 0  
            # train_from_test_dev[ index ].append( move_to_train )
            # new_test_dev[ index ].append( this_keep_here )

            
            
            this_move += len( move_to_train )
            this_keep += len( this_keep_here )

            
        print( "index, move, keep:", index, this_move, this_keep ) 

    
    # Extract one positive and one negative from this set for training

    # train_from_test_dev = [ list(), list() ]
    # new_test_dev        = [ list(), list() ]
    # for index in range( 2 ) :
    #     process_data = [ test, dev ]
    #     for idiom in process_data[ index ] :
    #         idiom_sents = len(idiom) 
    #         meanings    = list( set( idiom[0][2:8] ) )
    #         try :
    #             meanings.remove( 'None' )
    #         except ValueError :
    #             pass
    #         meanings_dict = dict()
    #         for meaning in meanings :
    #             meanings_dict[ meaning ] = list()
    #         for sent in idiom :
    #             try : 
    #                 meanings_dict[ sent[9] ].append( sent )
    #             except KeyError :
    #                 ## Someone tagged it as idiomatic when we decided it was only literal!
    #                 idiom_sents -= 1
    #                 continue

    #         need = [ 0, 1 ]
    #         counts = { 0 : 0, 1 : 0 }
    #         for meaning in meanings_dict.keys() :
    #             for sent in meanings_dict[ meaning ] :
    #                 counts[ sent[ 8 ] ] += 1

    #         new_need = list()
    #         for label in need :
    #             if counts[ label ] > 1 :
    #                 new_need.append( label )
    #         need = new_need
    #         move_to_train = list()
            
    #         this_idiom_sents       = list()
    #         this_idiom_sents_train = list()
    #         for meaning in meanings_dict.keys() :
    #             for sent in meanings_dict[ meaning ] :
    #                 if sent[ 8 ] in need : 
    #                     this_idiom_sents_train.append( sent )
    #                     need.remove( sent[ 8 ] )
    #                 else :
    #                     this_idiom_sents.append( sent ) 
                    
    #         this_keep_here = this_idiom_sents
    #         move_to_train  = this_idiom_sents_train
    #         assert idiom_sents == ( len( this_keep_here ) + len( move_to_train ) )
    #         assert len( this_keep_here ) > 0

    #         train_from_test_dev[ index ].append( move_to_train )
    #         new_test_dev[ index ].append( this_keep_here )
            


    train_from_test = train_from_test_dev[0]
    test            = new_test_dev[0]

    data  = {
        'test'           : test            ,
        'train_one_shot' : train_from_test  ,
    }

    assert len( data[ 'test' ] ) == len( data[ 'train_one_shot' ] ) == 50

    return data






def split_idiom_data_old( idiom_data, compositionality, language ) :


    raise Exception( "How do you know the test and dev you pick are also in idiom_data? dev test picked from compositionality -- you got lucky here." )
    
    compositionality_split = dict()
    for split in range( 1, 6 ) :
        compositionality_split[ split ] = \
                [ i for i in compositionality.keys()
                  if compositionality[ i ] <= split and compositionality[ i ] > ( split - 1 )
                 ]
    ## Add 0 to 1 
    compositionality_split[ 1 ] += [ i for i in compositionality.keys() if compositionality[ i ] == 0 ]

    [ random.shuffle( compositionality_split[ i ] ) for i in compositionality_split.keys() ]
    ## First extract "good test set" so we can use it later. 

    keep_counts = {
        'en' : {
            1 : 10,
            2 : 11,
            3 :  9,
            4 : 10,
            5 : 10
        },
        'pt' :  {
            1 : 10,
            2 : 11,
            3 :  9,
            4 : 10,
            5 : 10
        }
    }


    
    keep_idioms = list()
    for key in keep_counts[ language ].keys() :
        keep_idioms += compositionality_split[ key ][ : keep_counts[ language ][ key ] ]
        compositionality_split[ key ] = compositionality_split[ key ][ keep_counts[ language ][ key ] : ]

    assert (
        (
            len( keep_idioms ) + sum( [ len( compositionality_split[ i ] ) for i in compositionality_split.keys() ] )
        ) == len( compositionality.keys() )
    )

    test_dev_split = {
        'en' : {
            1 : [ 7, 7 ], 
            2 : [ 2, 2 ], 
            3 : [ 1, 0 ], 
            4 : [ 1, 1 ], 
            5 : [ 9, 10 ],
            'r' : [ 11, 10 ]  # We exclude one that is annotated by them. 
        }
    }

    test_idioms = list()
    dev_idioms  = list()
    for key in test_dev_split[ language ] :
        if key != 'r' : 
            test_idioms           += compositionality_split[ key ][ : test_dev_split[ language ][ key ][ 0 ] ]
            compositionality_split[ key ] = compositionality_split[ key ][ test_dev_split[ language ][ key ][ 0 ] : ]

            dev_idioms            += compositionality_split[ key ][ : test_dev_split[ language ][ key ][ 1 ] ]
            compositionality_split[ key ] = compositionality_split[ key ][ test_dev_split[ language ][ key ][ 0 ] : ]
            

    random.shuffle( idiom_data ) 

    train = list()
    dev   = list()
    test  = list()
    for one_idiom_data in idiom_data :
        this_idiom = one_idiom_data[ 0 ][ 1 ]
        if this_idiom in keep_idioms :
            continue
        
        if this_idiom in test_idioms :
            test.append( one_idiom_data )
            continue
        if this_idiom in dev_idioms :
            dev.append(  one_idiom_data )
            continue
        
        if test_dev_split[ language ][ 'r' ][0] != 0 :
            test.append( one_idiom_data )
            test_dev_split[ language ][ 'r' ][0] -= 1
            continue
        if test_dev_split[ language ][ 'r' ][1] != 0 :
            dev.append( one_idiom_data )
            test_dev_split[ language ][ 'r' ][1] -= 1
            continue

        train.append( one_idiom_data ) 


    ## Now remove from test and dev elements for training.
    train_from_test_dev = [ list(), list() ]
    new_test_dev        = [ list(), list() ]
    for index in range( 2 ) :
        process_data = [ test, dev ]
        this_move    = 0
        this_keep    = 0
        for idiom in process_data[ index ] :
            idiom_sents = len(idiom) 
            meanings = list( set( idiom[0][2:8] ) )
            try :
                meanings.remove( 'None' )
            except ValueError :
                pass
            meanings_dict = dict()
            for meaning in meanings :
                meanings_dict[ meaning ] = list()
            for sent in idiom :
                try : 
                    meanings_dict[ sent[9] ].append( sent )
                except KeyError :
                    ## Someone tagged it as idiomatic when we decided it was only literal!
                    idiom_sents -= 1
                    continue 

            move_to_train = list()
            for meaning in meanings :
                examples_of_this_meaning = len( meanings_dict[ meaning ] )
                to_train_count           = int( 0.25 *  len( meanings_dict[ meaning ] ) )
                if to_train_count == 0 and examples_of_this_meaning > 1 :
                    to_train_count = 1
                move_to_train += meanings_dict[ meaning ][ : to_train_count ] 
                meanings_dict[ meaning ] = meanings_dict[ meaning ][ to_train_count : ]

            this_keep_here = list()
            for meaning in meanings_dict.keys() :
                this_keep_here += meanings_dict[ meaning ]

            assert idiom_sents == ( len( this_keep_here ) + len( move_to_train ) )
            assert len( this_keep_here ) > 0 
            train_from_test_dev[ index ].append( move_to_train )
            new_test_dev[ index ].append( this_keep_here )
            
            this_move +=  len( move_to_train )
            this_keep += len( this_keep_here ) 
        print( "move, keep:", index, this_move, this_keep ) 

    
    # Extract one positive and one negative from this set for training

    # train_from_test_dev = [ list(), list() ]
    # new_test_dev        = [ list(), list() ]
    # for index in range( 2 ) :
    #     process_data = [ test, dev ]
    #     for idiom in process_data[ index ] :
    #         idiom_sents = len(idiom) 
    #         meanings    = list( set( idiom[0][2:8] ) )
    #         try :
    #             meanings.remove( 'None' )
    #         except ValueError :
    #             pass
    #         meanings_dict = dict()
    #         for meaning in meanings :
    #             meanings_dict[ meaning ] = list()
    #         for sent in idiom :
    #             try : 
    #                 meanings_dict[ sent[9] ].append( sent )
    #             except KeyError :
    #                 ## Someone tagged it as idiomatic when we decided it was only literal!
    #                 idiom_sents -= 1
    #                 continue

    #         need = [ 0, 1 ]
    #         counts = { 0 : 0, 1 : 0 }
    #         for meaning in meanings_dict.keys() :
    #             for sent in meanings_dict[ meaning ] :
    #                 counts[ sent[ 8 ] ] += 1

    #         new_need = list()
    #         for label in need :
    #             if counts[ label ] > 1 :
    #                 new_need.append( label )
    #         need = new_need
    #         move_to_train = list()
            
    #         this_idiom_sents       = list()
    #         this_idiom_sents_train = list()
    #         for meaning in meanings_dict.keys() :
    #             for sent in meanings_dict[ meaning ] :
    #                 if sent[ 8 ] in need : 
    #                     this_idiom_sents_train.append( sent )
    #                     need.remove( sent[ 8 ] )
    #                 else :
    #                     this_idiom_sents.append( sent ) 
                    
    #         this_keep_here = this_idiom_sents
    #         move_to_train  = this_idiom_sents_train
    #         assert idiom_sents == ( len( this_keep_here ) + len( move_to_train ) )
    #         assert len( this_keep_here ) > 0

    #         train_from_test_dev[ index ].append( move_to_train )
    #         new_test_dev[ index ].append( this_keep_here )
            


            
    # Validate training data
    new_train = list()
    for idiom in train : 
        meanings = list( set( idiom[0][2:8] ) )
        meanings_dict = dict()
        
        for meaning in meanings :
            meanings_dict[ meaning ] = list()
        for sent in idiom :
            try : 
                meanings_dict[ sent[9] ].append( sent )
            except KeyError :
                ## Someone tagged it as idiomatic when we decided it was only literal!
                continue 

        this_update_idiom = list()
        for meaning in meanings_dict.keys() :
            this_update_idiom += meanings_dict[ meaning ]
        assert  len( this_update_idiom ) > 0
        new_train.append( this_update_idiom )

    train                           = new_train
    train_from_test, train_from_dev = train_from_test_dev
    test           , dev            = new_test_dev

    data  = {
        'test'            : test            ,
        'train'           : train           ,
        'dev'             : dev             ,
        'train_from_test' : train_from_test ,
        'train_from_dev'  : train_from_dev  ,
    }

    return data


def _filter_idiom_data_for_test( idiom_data, trail_data_location ) :

    with open( trail_data_location, encoding='utf-8') as fh:
        trail_data = json.load(fh)

    all_trail_idioms = list()
    for data_split in trail_data.keys() :
        for elem in trail_data[ data_split ] : 
            all_trail_idioms.append( elem[0][1] )
    all_trail_idioms = set( all_trail_idioms )

    idiom_data_idioms = list()
    for elem in idiom_data:
        idiom_data_idioms.append( elem[0][1] )

    test_idioms = set( idiom_data_idioms ) - all_trail_idioms

    assert len( test_idioms ) == 50

    ## Now extract only these.
    test_idiom_data = list()
    for elem in idiom_data :
        if elem[0][1] in test_idioms :
            test_idiom_data.append( elem )

    return test_idiom_data
    

def _cut_to_size( idiom_data, size ) :

    ## Get idioms we can drop from
    ## [['días hábiles', 16], ['paseo marítimo', 16], ['banda sonora', 17], ['luz vermella', 17], ['xente nova', 17], ['incendios forestais', 18], ['monte baixo', 18], ['camisa branca', 19], ['casco antigo', 19], ['centro neurálxico', 19], ['festa rachada', 19], ['memoria viva', 19], ['porta grande', 19], ['renda básica', 19], ['tempo parcial', 19], ['vida real', 19], ['aire libre', 20], ['aviso amarelo', 20], ['banda ancha', 20], ['brazos abertos', 20], ['cidade vella', 20], ['fenda dixital', 20], ['golpe duro', 20], ['horas baixas', 20], ['leña verde', 20], ['lingua galega', 20], ['lume lento', 20], ['luz verde', 20], ['masa salarial', 20], ['materia escura', 20], ['pegada ecolóxica', 20], ['poboación activa', 20], ['salto cualitativo', 20], ['vida laboral', 20], ['glóbulos vermellos', 21]]

    ## Each idiom will have 14, and 12 of them will have 15 for a total of 712


    raise Exception( "Cut down here" )

    idiom_counts = list()
    for one_idiom_data in idiom_data :
        idiom_counts.append( [ one_idiom_data[0][1], len( one_idiom_data ) ] )
    idiom_counts = sorted( idiom_counts, key=lambda x:x[1] )
    print( idiom_counts ) 


    # new_idiom_data = list()
    # for one_idiom_data in idiom_data :
        
    
    import pdb; pdb.set_trace()
    print()
   
if __name__ == '__main__' :
    
    language     = 'gl' 
    table        = 'annotations_p3' ## Pick annotations and annotations_p2 for cohan kappa
    
    idiom_data   = get_data( language, table )
    idiom_data   = _cut_to_size( idiom_data, size=713 )
    
    assert len( idiom_data ) == 50 
    data = split_idiom_data( idiom_data, language )


    outfile = None
    if table == 'annotations_p3' :
        outfile = 'gl_idiom_data_TEST_v3.pk3'
    else :
        outfile = 'gl_idiom_data_' + table + '_v3.pk3'
        
    pickle.dump( data, open( outfile, 'wb' ) )
    print( "Wrote train test data to: ", outfile )




    print ( """

---------------------------------------------
                   TODO
---------------------------------------------

1. Check that one shot has picked the corret data. 
2. Check that the correct idioms got picked here. 
    2.1 Make sure there is no overlap with released data. 
3. Run specific checks for stuff with "X"
    3.1 Make sure you "get" what "X" is (Those that are only literal, and so the second meaning becomes primary). 
    3.2 Make sure that you manually check the idiom data (all of them). 

Important todo: 
   ** cohen_kappa_score ** 

Ed to check meanings of: 



""" ) 
    
    

    sys.exit()
