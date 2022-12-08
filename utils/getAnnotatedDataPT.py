import re
import os
import csv
import sys
import json
import pickle

base_path  = '../'
utils_path = os.path.join( os.path.dirname( os.path.realpath(__file__) ), base_path + "utils")
sys.path.append( utils_path )

from MyMySQL                import MyMySQL
mysql_obj = MyMySQL(config_path=utils_path)

import random
random.seed( 42 )


all_idioms_in_annotation_set = list()

def load_new_meanings( language ) :
    location = None
    if language == 'pt' : 
        location = 'data/PortugueseNewMeanings.csv'
    else :
        raise Exception( "Do not have update file" )

    idioms   = dict()
    header   = None
    # ['MWE', 'Literal Meaning', 'Non-Literal Meaning', 'Is compositional', '', 'NEW Literal Meaning', 'NEW Non-Literal Meaning', 'Non-Literal Meaning Added',
    with open( location ) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if header is None :
                header = row
                continue
            idiom = row[0]
            idiom = re.sub( r'\s\s', ' ', idiom )
            idioms[ idiom ] = dict()
            idioms[ idiom ][ 'meanings_old' ] = [ row[header.index( 'Literal Meaning' )], row[ header.index( 'Non-Literal Meaning' ) ] ]
            new_non_literal_meaning           = row[ header.index( 'NEW Non-Literal Meaning' ) ]
            keep                              = row[header.index( 'Is compositional' )]
            if keep != 'I' :
                if new_non_literal_meaning == 'None' :
                    keep = 'X'
                    # new_non_literal_meaning = ''
            idioms[ idiom ][ 'keep'         ] = keep
            idioms[ idiom ][ 'meanings_new' ] = [ row[ header.index( 'NEW Literal Meaning' ) ], new_non_literal_meaning ]

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


def _get_agree_data( table1_data, table1_counts, table2_data, table2_counts ) :

    assert len( table1_data ) == len( table2_data )

    ## Must take meanings from table2 (table1 is in different order, came from database
    annotation_index   = 9
    target_sent_index = 11
    
    agree_idioms = list()
    agree_data   = list()
    no_agree     = list()
    annon1_all   = list()
    annon2_all   = list()
    for idiom_index in range( len( table1_data ) ) :
        assert table1_data[ idiom_index ][0][1] == table2_data[ idiom_index ][0][1] ## Idiom must be equal
        assert len( table1_data[ idiom_index ] ) == len( table2_data[ idiom_index ] )
        this_disag = 0
        this_idiom_agree_sents = list()
        all_idioms_in_annotation_set.append( table2_data[ idiom_index ][ 0 ][ 1 ] )
        for sent_index in range( len( table1_data[ idiom_index ] ) ) :
            assert table1_data[ idiom_index ][ sent_index ][ target_sent_index ] == table2_data[ idiom_index ][ sent_index ][ target_sent_index ]
            annon1 = table1_data[ idiom_index ][ sent_index ][ annotation_index ]
            annon2 = table2_data[ idiom_index ][ sent_index ][ annotation_index ]
            if annon1 == annon2 :
                agree_data.append( table2_data[idiom_index][sent_index] )
                this_idiom_agree_sents.append( table2_data[idiom_index][sent_index] ) 
            else :
                no_agree.append( table2_data[idiom_index][sent_index] )
                this_disag += 1
            annon1_all.append( annon1 )
            annon2_all.append( annon2 )
        assert table1_data[ idiom_index ][0][2] != table1_data[ idiom_index ][0][3]
        agree_idioms.append( this_idiom_agree_sents )
                
    from sklearn.metrics import cohen_kappa_score
    print( "Agree, No Agree", len( agree_data ), len( no_agree ) )
    print( "Cohan Kappa", cohen_kappa_score( annon1_all, annon2_all ) )


    ## Data clean - first get rid of 'Discard' and remove dups

    existing_sents = list()
    clear_data     = list()
    low_freq       = list()
    for idiom_index in range( len( agree_idioms ) ) :
        this_idiom_new_sents = list()
        for sent_index in range(  len( agree_idioms[ idiom_index ] ) ) :
           this_label = agree_idioms[ idiom_index ][ sent_index ][ annotation_index ]
           if this_label == 'Discard' :
               continue
           if agree_idioms[ idiom_index ][ sent_index ][ target_sent_index ].lower() in set( existing_sents ) :
               continue
           existing_sents.append( agree_idioms[ idiom_index ][ sent_index ][ target_sent_index ].lower() )
           this_idiom_new_sents.append( agree_idioms[ idiom_index ][ sent_index ] )
        if len( this_idiom_new_sents ) < 10 :
            if len( this_idiom_new_sents ) < 5 :
                continue
            low_freq.append( this_idiom_new_sents )
            continue
        clear_data.append( this_idiom_new_sents )


    clear_data = low_freq + clear_data

    print( "Total Idioms", len( clear_data ) )

    return annon1_all, annon2_all, clear_data

def get_data( table1, table2, split ) :

    table1_counts = table1_data = None
    if not table1 is None :
        table1_data, table1_counts = get_data_from_single_table( table1 )
        if not split :
            return table1_data
        
        
    table2_counts = table2_data = None
    if not table2 is None : 
        table2_data, table2_counts = get_data_from_single_table( table2 )
        if not split :
            return table2_data

    ## Data validation

    assert len( table1_data ) == len( table1_counts ) == len( table2_data ) == len( table2_counts )

    for idiom_index in range( len( table1_data ) ) :
        assert len( table1_data[idiom_index] ) == table1_counts[ idiom_index ][-1] 
        assert len( table2_data[idiom_index] ) == table2_counts[ idiom_index ][-1]
        if table1_counts[ idiom_index ][-1] != table2_counts[ idiom_index ][-1] :
            import pdb; pdb.set_trace()

    return _get_agree_data( table1_data, table1_counts, table2_data, table2_counts )


def _get_annotations_table_data( annotations, meanings ) :

    meanings = sorted( meanings, key=lambda x:x[0] )
    
    if len( annotations ) != len( meanings ) :
        ## Meaning added by annotator 2
        meanings = meanings[ :len( annotations ) ]
    assert len( annotations ) == len( meanings )
    
    labels        = list()
    ann_meanings  = list()
    ann_sentences = list()

    for meaning in meanings :
        this_meaning_id = meaning[0]
        this_meaning    = meaning[-1]
        if this_meaning == 'Outro (other)' :
            this_meaning = 'Discard'
        ann_meanings.append( [ this_meaning_id, this_meaning ] )

    for meaning_index in range( len( meanings ) ) :
        for single_this_meaning_annotation in annotations[ meaning_index ] :
            ann_sentences.append( single_this_meaning_annotation )
            labels.append( ann_meanings[ meaning_index ][0] )
    
    return labels, ann_meanings, ann_sentences 


def get_data_from_single_table( table, language='pt' ) : 

    idiom_new_meanings = load_new_meanings( language )
   
    query   = "SELECT idiom_id, idiom FROM idioms WHERE language = '" + language + "';"
    results = list( reversed( mysql_obj.mysql_get( query ) ) )

    idiom_data   = list()
    idiom_counts = list()
    for idiom_id, idiom in results :

        try : 
            if idiom_new_meanings[ idiom ][ 'keep' ] == "I" :
                print( "Ignoring idiom {} as per update file.".format( idiom ), file=sys.stderr ) 
                continue
        except KeyError :
            import pdb; pdb.set_trace()
            
        
        query    = "SELECT meaning_id, idiom_id, meaning FROM meanings WHERE idiom_id = " + str( idiom_id ) + " ORDER BY meaning_id DESC;"
        meanings = list( reversed( mysql_obj.mysql_get( query ) ) )

        query    = "SELECT data FROM " + table + " WHERE idiom_id = " + str( idiom_id ) + ";"
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

        labels   = ann_meanings = ann_sentences = None
        if table == 'annotations' :
            labels, ann_meanings, ann_sentences = _get_annotations_table_data( annotations, meanings )
        else : 
            labels        = annotations[ 'annotations' ]
            ann_meanings  = annotations[ 'meanings'    ]
            ann_sentences = annotations[ 'sentences'   ]


        ## validate labels
        meanings_dict    = dict()
        id_meanings_dict = dict()
        meanings_from_update_file = idiom_new_meanings[ idiom ][ 'meanings_old' ]
        for this_meaning_id, this_idiom_id, this_meaning in meanings :
            assert this_idiom_id == idiom_id
            if this_meaning == 'Outro (other)' :
                this_meaning = 'Discard'
            meanings_dict[ this_meaning_id ] = this_meaning
            id_meanings_dict[ this_meaning ] = this_meaning_id

        for this_meaning_id, this_meaning in ann_meanings :
            ## This meaning was added to the system by mistake and was used by some annotators! 
            if this_meaning_id in [ 2365 ] :
                print( "ERROR: You should remove the idiom {} for now.".format( idiom ) )
                sys.exit()
            if meanings_dict[ this_meaning_id ] != this_meaning :
                import pdb; pdb.set_trace()
            try : 
                assert meanings_dict[ this_meaning_id ] == this_meaning
            except KeyError :
                print( "Meaning mismatch debug", file=sys.stderr )
                import pdb; pdb.set_trace()

        ## End of validation
 
        is_only_literal = False
        if idiom_new_meanings[ idiom ][ 'keep' ] == 'X' or idiom_new_meanings[ idiom ][ 'meanings_new' ][1] == 'None' :
            is_only_literal = True

        meanings = list()
        if not is_only_literal : 
            for index in range( 2 ) :
                new_meaning = idiom_new_meanings[ idiom ][ 'meanings_new' ][ index ]
                if not new_meaning == '' : 
                    ann_meanings[ index ][1] = new_meaning
            meanings = ann_meanings[:2]
        else :
            if idiom_new_meanings[ idiom ][ 'meanings_new' ][1] != 'None' :
                import pdb; pdb.set_trace()
            assert idiom_new_meanings[ idiom ][ 'meanings_new' ][1] == 'None'
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

            ## Must do this when getting agreement
            # if split and label_meaning == 'Discard' :
            #     continue

            is_literal    = None
            if meanings[0][1] == label_meaning or label_meaning == 'Proper Noun' :
                is_literal = 1
            else :
                is_literal = 0

            assert not label_meaning is None
            assert not is_literal    is None

            
            this_sent_row.append( is_literal    )
            this_sent_row.append( label_meaning )

            ## Postprocessing -- Not required for PT data?
            # for sent_index in range( 3 ) :
            #     prev_sent, this_sent, next_sent  = _post_process_sent( ann_sentences[ index ][ 'data' ][ sent_index ], sent_index, idiom )
            #     if not prev_sent is None :
            #         assert sent_index == 1 
            #         ann_sentences[ index ][ 'data' ][ sent_index - 1 ] = prev_sent
            #     if not next_sent is None :
            #         assert sent_index == 1 
            #         ann_sentences[ index ][ 'data' ][ sent_index     ] = this_sent
            #         ann_sentences[ index ][ 'data' ][ sent_index + 1 ] = next_sent
            #         break
            #     ann_sentences[ index ][ 'data' ][ sent_index     ] = this_sent

            this_sent_row += ann_sentences[ index ][ 'data' ]

            required_len = 14
            if not split :
                required_len = 15
            if len( this_sent_row ) != required_len :
                print( "ERROR with len", this_sent_row, len( this_sent_row ) )
                sys.exit() 

            assert len( this_sent_row ) == required_len

            # Remove duplicates in merge
            # this_entry = ann_sentences[ index ][ 'data' ][1].lower()
            # if this_entry in added_sents :
            #     continue
            # else : 
            #     added_sents.append( this_entry )
            idiom_rows.append( this_sent_row )

        idiom_data.append( idiom_rows )
        idiom_counts.append( [ idiom, len( idiom_rows ) ] ) ## Debug info


    return idiom_data, idiom_counts


def _load_compositionality( language ) :

    idiom_compositionality = dict()
    location = 'data/' + language + '.filtered.csv' 
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

    all_idioms = list()
    for one_idiom_data in idiom_data :
        this_idiom = one_idiom_data[ 0 ][ 1 ] 
        all_idioms.append( this_idiom ) 

    new_compositionality = dict()
    for comp_idiom in compositionality.keys() :
        if comp_idiom in all_idioms_in_annotation_set : 
            new_compositionality[ comp_idiom ] = compositionality[ comp_idiom ]
    compositionality = new_compositionality
    
    compositionality_split = dict()
    for split in range( 1, 6 ) :
        compositionality_split[ split ] = \
                [ i for i in compositionality.keys()
                  if compositionality[ i ] <= split and compositionality[ i ] > ( split - 1 ) 
                 ]
    ## Add 0 to 1 
    compositionality_split[ 1 ] += [ i for i in compositionality.keys() if compositionality[ i ] == 0 ]


    all_comp_idioms = list()
    for compositionality_key in compositionality_split.keys() :
        all_comp_idioms += compositionality_split[ compositionality_key ]
    # sys.exit()



    # sort by bad:
    for split in compositionality_split.keys() :
        compositionality_split[ split ] = sorted( compositionality_split[ split ], key=lambda x:len(x) )
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


    ## Try to keep those not in all_idioms
    keep_idioms = list()
    for key in keep_counts[ language ].keys() :
        this_key_compositionality_new= list()
        for this_comp_idiom in compositionality_split[ key ] :
            if keep_counts[ language ][ key ] > 0 and not this_comp_idiom in all_idioms :
                keep_idioms.append( this_comp_idiom )
                keep_counts[ language ][ key ] -= 1
            else :
                this_key_compositionality_new.append( this_comp_idiom )

        if keep_counts[ language ][ key ] > 0 :
            keep_idioms += this_key_compositionality_new[ :keep_counts[ language ][ key ]]
            this_key_compositionality_new = this_key_compositionality_new[ keep_counts[ language ][ key ] : ]
                
        compositionality_split[ key ] = this_key_compositionality_new

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
        },
        'pt' : {
            1 : [ 5, 5 ], 
            2 : [ 2, 2 ], 
            3 : [ 1, 1 ], 
            4 : [ 1, 1 ], 
            5 : [ 5, 5 ],
            'r' : [ 6, 6 ] 
        }
    }

    test_idioms = list()
    dev_idioms  = list()
    for key in test_dev_split[ language ] :
        if key != 'r' : 
            # test_idioms           += compositionality_split[ key ][ : test_dev_split[ language ][ key ][ 0 ] ]
            # compositionality_split[ key ] = compositionality_split[ key ][ test_dev_split[ language ][ key ][ 0 ] : ]
            this_key_compositionality_split_remaining = list()
            for single_idiom in compositionality_split[ key ] :
                if not single_idiom in all_idioms :
                    continue
                if test_dev_split[ language ][ key ][ 0 ] > 0 :
                    test_idioms.append( single_idiom )
                    test_dev_split[ language ][ key ][ 0 ] -= 1
                    continue
                this_key_compositionality_split_remaining.append( single_idiom ) 
                
            compositionality_split[ key ] = this_key_compositionality_split_remaining

            # dev_idioms            += compositionality_split[ key ][ : test_dev_split[ language ][ key ][ 1 ] ]
            # compositionality_split[ key ] = compositionality_split[ key ][ test_dev_split[ language ][ key ][ 0 ] : ]
            
            this_key_compositionality_split_remaining = list()
            for single_idiom in compositionality_split[ key ] :
                if not single_idiom in all_idioms :
                    continue
                if test_dev_split[ language ][ key ][ 1 ] > 0 :
                    dev_idioms.append( single_idiom )
                    test_dev_split[ language ][ key ][ 1 ] -= 1
                    continue
                this_key_compositionality_split_remaining.append( single_idiom ) 
                
            compositionality_split[ key ] = this_key_compositionality_split_remaining


    random.shuffle( idiom_data )


    train = list()
    dev   = list()
    test  = list()
    dev_add_act  = 0
    dev_add_rand = 0
    for one_idiom_data in idiom_data :
        this_idiom = one_idiom_data[ 0 ][ 1 ]
        if this_idiom in keep_idioms :
            continue
        
        if this_idiom in test_idioms :
            test.append( one_idiom_data )
            continue
        if this_idiom in dev_idioms :
            dev_add_act += 1
            dev.append(  one_idiom_data )
            continue
        
        if test_dev_split[ language ][ 'r' ][0] != 0 :
            test.append( one_idiom_data )
            test_dev_split[ language ][ 'r' ][0] -= 1
            dev_add_rand += 1
            continue
        if test_dev_split[ language ][ 'r' ][1] != 0 :
            dev.append( one_idiom_data )
            test_dev_split[ language ][ 'r' ][1] -= 1
            continue

        train.append( one_idiom_data ) 

    assert len( set( all_idioms ) - set(keep_idioms ) ) == ( len( train ) + len( dev ) + len( test ) ) 

    ## Now remove from test and dev elements for training.
    train_from_test_dev = [ list(), list() ]
    new_test_dev        = [ list(), list() ]
    for index in range( 2 ) :
        process_data = [ test, dev ]
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
            if idiom_sents == 0 :
                print( "No sents", idiom[0][1] )
                continue
            assert len( this_keep_here ) > 0  
            train_from_test_dev[ index ].append( move_to_train )
            new_test_dev[ index ].append( this_keep_here )
            
            this_move +=  len( move_to_train )
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
        if len( this_update_idiom ) == 0 :
            print( "No sents train", idiom[0][1] )

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

    assert len( data[ 'test' ] ) == len( data[ 'train_from_test' ] ) == 20 
    assert len( data[ 'dev'  ] ) == len( data[ 'train_from_dev'  ] ) == 20 

    return data

   
if __name__ == '__main__' :
    
    language     = 'pt' 
    table1       = 'annotations'
    table2       = 'annotations_p2'

    split        = True ## Should always be true. (used for debug)
    if not split :
        if not table1 is None and not table2 is None :
            raise Exception( "If extracting single annotator data, you must specify only one table" )
    
    annon1_all, annon2_all, clear_data  = get_data( table1, table2, split ) # annon1_all, annon2_all, agree_data

    for annon_index in range( 2 ) :
        data = None
        if annon_index == 0 :
            data = annon1_all
        if annon_index == 1 :
            data = annon2_all
        assert not data is None
        outfile = language + '_annon_' + str( annon_index ) + '_data.pk3'
        pickle.dump( data, open( outfile, 'wb' ) )
        print( "Wrote raw idiom data to: ", outfile ) 


    if split : 
        idiom_compositionality = _load_compositionality( language )
        data                   = split_idiom_data( clear_data, idiom_compositionality, language )


        outfile = 'pt_idiom_data_v3.pk3'
        pickle.dump( data, open( outfile, 'wb' ) )
        print( "Wrote train test data to: ", outfile )

    sys.exit()
