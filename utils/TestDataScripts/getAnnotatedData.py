import re
import os
import csv
import sys
import json
import pickle

base_path  = '../../'
utils_path = os.path.join( os.path.dirname( os.path.realpath(__file__) ), base_path + "utils")
sys.path.append( utils_path )

from MyMySQL                import MyMySQL
mysql_obj = MyMySQL(config_path=utils_path)

import random
random.seed( 42 ) 

def load_new_meanings( language ) :
    location = None
    if language == 'en' : 
        location = '../data/EnglishNewMeaningsTest.csv'
    else :
        raise Exception( "Do not have update file" )
    
    idioms   = dict()
    with open( location ) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            idioms[ row[0] ] = dict()
            idioms[ row[0] ][ 'meanings_old' ] = [ row[1], row[2] ]
            idioms[ row[0] ][ 'keep'         ] = row[3]
            idioms[ row[0] ][ 'meanings_new' ] = row[14:]

    return idioms


def _post_process_sent( sent, sent_index, idiom ) :

    sent = sent.replace( '_', '' ) 
    sent = sent.replace( '**', '' ) 
    sent = sent.replace( ' &gt; ', ' ' )
    sent = sent.replace( '&gt;', '' )
    sent = sent.replace( '&amp;', '&' )
    
    split_sent = re.split( '\.["”]', sent )
    clean_split_sent = [ i for i in split_sent if not i in [ '', ' ' ] ]
    if len( clean_split_sent ) > 1 :

        right_sent = None
        close_quote = False
        for sent_part in reversed( split_sent ) :
            if sent_part in [ '',  ' ' ] :
                close_quote = True
                continue
            right_sent = sent_part
            break
        assert not right_sent is None
        if close_quote :
            right_sent += '."' if '."' in sent else '.”'
        right_sent = right_sent.lstrip().rstrip()

        left_sent   = split_sent[0]
        left_sent += '."' if '."' in sent else '.”'
        left_sent  = left_sent.lstrip().rstrip()

        if sent_index == 0 :
            assert not right_sent in ['', ' ' ]
            return None, right_sent, None
        if sent_index == 2 :
            assert not left_sent  in ['', ' ' ]
            return None, left_sent , None

        prev_sent  = None
        next_sent  = None
        idiom_sent = None
        for idiom_sent_split_index in range( len( split_sent ) ) :
            if idiom in split_sent[ idiom_sent_split_index ].lower() :
                idiom_sent = split_sent[ idiom_sent_split_index ]
                idiom_sent = idiom_sent.rstrip().lstrip()
                if ( idiom_sent_split_index ) + 1 != len( split_sent ) :
                    next_sent = split_sent[ idiom_sent_split_index + 1 ]
                    next_sent = next_sent.rstrip().lstrip()
                    if next_sent == '' :
                        next_sent = None
                    if ( idiom_sent_split_index + 2 )!= len( split_sent ) :
                        next_sent += '."' if '."' in sent else '.”'
                    idiom_sent += '."' if '."' in sent else '.”'
                if idiom_sent_split_index != 0 :
                    for sent_part in reversed( split_sent[ : idiom_sent_split_index ] ) :
                        if sent_part in [ '', ' ' ] :
                            continue
                        else :
                            prev_sent = sent_part.lstrip().rstrip()
                            prev_sent += '."' if '."' in sent else '.”'
                return prev_sent, idiom_sent, next_sent
        if idiom_sent is None :
            raise Exception ( "Must have found idiom by now!" )

    return None, sent, None


def get_data( language, user_id, table, split ) : 

    idiom_new_meanings = load_new_meanings( language )
   
    query   = "SELECT idiom_id, idiom FROM idioms WHERE language = '" + language + "';"
    results = list( reversed( mysql_obj.mysql_get( query ) ) )

    idiom_data = list()
    for idiom_id, idiom in results :

        if idiom_new_meanings[ idiom ][ 'keep' ] == "I" :
            print( "Ignoring idiom {} as per update file.".format( idiom ), file=sys.stderr ) 
            continue
        
        query    = "SELECT meaning_id, idiom_id, meaning FROM meanings WHERE idiom_id = " + str( idiom_id ) + " ORDER BY meaning_id DESC;"
        meanings = list( reversed( mysql_obj.mysql_get( query ) ) )

        query    = "SELECT data FROM " + table + " WHERE user_id = " + str( user_id ) + " and idiom_id = " + str( idiom_id ) + ";"
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
        
        ## validate labels
        meanings_dict    = dict()
        id_meanings_dict = dict()
        meanings_from_update_file = idiom_new_meanings[ idiom ][ 'meanings_old' ]
        for this_meaning_id, this_idiom_id, this_meaning in meanings :
            assert this_idiom_id == idiom_id
            if this_meaning == 'Other' :
                this_meaning = 'Discard'
            meanings_dict[ this_meaning_id ] = this_meaning
            id_meanings_dict[ this_meaning ] = this_meaning_id

        for this_meaning_id, this_meaning in ann_meanings :
            try : 
                assert meanings_dict[ this_meaning_id ] == this_meaning
            except KeyError :
                print( "Meaning mismatch debug", file=sys.stderr )
                import pdb; pdb.set_trace()

        ## End of validation
 
        is_only_literal = False
        if idiom_new_meanings[ idiom ][ 'keep' ] == 'X' or idiom_new_meanings[ idiom ][ 'meanings_new' ][0] == 'None' :
            is_only_literal = True

        meanings = list()
        if not is_only_literal : 
            for index in range( 2 ) :
                new_meaning = idiom_new_meanings[ idiom ][ 'meanings_new' ][ index ]
                if not new_meaning == '' : 
                    ann_meanings[ index ][1] = new_meaning
            meanings = ann_meanings[:2]
        else :
            if idiom_new_meanings[ idiom ][ 'meanings_new' ][0] != 'None' :
                import pdb; pdb.set_trace()
            assert idiom_new_meanings[ idiom ][ 'meanings_new' ][0] == 'None'
            meanings = [ ann_meanings[1], [ 0, 'None' ] ]

        meanings += ann_meanings[5:]
        meanings += [[ 0, 'None'] ] * ( 4 - len( meanings ) )
        if split : 
            meanings += [ i for i in ann_meanings[2:5] if i[1] != 'Discard' ]
        else : 
            meanings += [ i for i in ann_meanings[2:5]                      ]

        meaning_len = 6
        if not split :
            meaning_len = 7
        if len( meanings ) != meaning_len :
            print( "Failed meaning len assert" )
            import pdb; pdb.set_trace()
        assert len( meanings ) == meaning_len

        idiom_rows = list()
        added_sents = list()
        for index in range( len( labels ) ) :

            this_sent_row = [ idiom_id, idiom ] + [ i[1] for i in meanings ]

            label_meaning = None
            for meaning in ann_meanings :
                if int( labels[ index ] ) == int( meaning[0] ) :
                    label_meaning = meaning[1]

            if split and label_meaning == 'Discard' :
                continue

            is_literal    = None
            if meanings[0][1] == label_meaning or label_meaning == 'Proper Noun' :
                is_literal = 1
            else :
                is_literal = 0

            assert not label_meaning is None
            assert not is_literal    is None

            
            this_sent_row.append( is_literal    )
            this_sent_row.append( label_meaning )

            ## Postprocessing
            for sent_index in range( 3 ) :
                prev_sent, this_sent, next_sent  = _post_process_sent( ann_sentences[ index ][ 'data' ][ sent_index ], sent_index, idiom )
                if not prev_sent is None :
                    assert sent_index == 1 
                    ann_sentences[ index ][ 'data' ][ sent_index - 1 ] = prev_sent
                if not next_sent is None :
                    assert sent_index == 1 
                    ann_sentences[ index ][ 'data' ][ sent_index     ] = this_sent
                    ann_sentences[ index ][ 'data' ][ sent_index + 1 ] = next_sent
                    break
                ann_sentences[ index ][ 'data' ][ sent_index     ] = this_sent

            this_sent_row += ann_sentences[ index ][ 'data' ]

            required_len = 14
            if not split :
                required_len = 15
            if len( this_sent_row ) != required_len :
                print( this_sent_row, len( this_sent_row ) )
                sys.exit()

            assert len( this_sent_row ) == required_len

            this_entry = ann_sentences[ index ][ 'data' ][1].lower()
            # this_entry = '. '.join( ann_sentences[ index ][ 'data' ] ).lower()
            if this_entry in added_sents :
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
            # assert len( this_keep_here ) > 0 
            # train_from_test_dev[ index ].append( move_to_train )
            # new_test_dev[ index ].append( this_keep_here )



            
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
            


            
    # # Validate training data
    # new_train = list()
    # for idiom in train : 
    #     meanings = list( set( idiom[0][2:8] ) )
    #     meanings_dict = dict()
        
    #     for meaning in meanings :
    #         meanings_dict[ meaning ] = list()
    #     for sent in idiom :
    #         try : 
    #             meanings_dict[ sent[9] ].append( sent )
    #         except KeyError :
    #             ## Someone tagged it as idiomatic when we decided it was only literal!
    #             continue 

    #     this_update_idiom = list()
    #     for meaning in meanings_dict.keys() :
    #         this_update_idiom += meanings_dict[ meaning ]
    #     assert  len( this_update_idiom ) > 0
    #     new_train.append( this_update_idiom )

    # train                           = new_train

    
    train_from_test = train_from_test_dev[0]
    test            = new_test_dev[0]

    data  = {
        'test'           : test            ,
        'train_one_shot' : train_from_test  ,
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
    
   
if __name__ == '__main__' :
    
    language     = 'en' 
    # user_id      =   9
    user_id      =   1
    # table        = 'annotations_p2'
    table        = 'annotations_p3'
    split        = True
    

    trail_data   = '/home/harish_idioms/EMNLP-2021/create_final_dataset/V2/EMNLP/TaskIndependentData/en_raw_data.json' 
    
    idiom_data   = get_data( language, user_id, table, split )
    idiom_data   = _filter_idiom_data_for_test( idiom_data, trail_data )

    assert len( idiom_data ) == 50  ## Only Test now. 
    
    outfile = language + '_' + str( user_id ) + '_' + table + '_TEST_data.pk3'
    pickle.dump( idiom_data, open( outfile, 'wb' ) )
    print( "Wrote raw idiom data to: ", outfile ) 

    if split : 
        idiom_compositionality = _load_compositionality( language )
        data                   = split_idiom_data( idiom_data, idiom_compositionality, language )


        outfile = 'en_idiom_data_TEST_v3.pk3'
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
4. Pay specific attention to:  Pocket book, engine room, time difference

Important todo: 
   ** cohen_kappa_score ** 

Ed to check meanings of: 
Record book, Research lab, 


""" ) 
        
    sys.exit()
