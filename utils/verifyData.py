import re
import os
import sys
import json
import pickle

base_path  = '../'
utils_path = os.path.join( os.path.dirname( os.path.realpath(__file__) ), base_path + "utils")
sys.path.append( utils_path )

from MyMySQL                import MyMySQL
mysql_obj = MyMySQL(config_path=utils_path)


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


def db_annotations( idiom ) : 

    query    = "select * from idioms where idiom = '" + idiom + "' ;"
    results  = list( reversed( mysql_obj.mysql_get( query ) ) )
    
    idiom_id = int( results[0][0] )

    query    = "SELECT data FROM annotations_p4 WHERE idiom_id = " + str( idiom_id ) + " order by annotation_id DESC limit 1;"
    results  = list( reversed( mysql_obj.mysql_get( query ) ) )
    if len( results ) == 0 :
        query    = "SELECT data FROM annotations_p3 WHERE idiom_id = " + str( idiom_id ) + " order by annotation_id DESC limit 1;"
        results  = list( reversed( mysql_obj.mysql_get( query ) ) )
    
    assert len( results ) > 0
    
    results  = results[-1][0]
    
    results  = re.sub( r'^\'', '', results )
    results  = re.sub( r'\'$', '', results )
    
    results = json.loads( results )

    if True : 

        # print( "Total", len( results[ 'annotations' ] ) )

    
        annotations = results[ 'annotations' ]
        meanings    = results[ 'meanings'    ]
        sentences   = results[ 'sentences'   ]

        ann_sentences = sentences

        for index in range( len( sentences ) ) : 
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


        sentences = ann_sentences
        sent_tags = list()
        for index in range( len( sentences ) ) :
            this_sent  = sentences[ index ][ 'data' ] #[1]
            this_label = [ i for i in meanings if i[0] == int( annotations[ index ] ) ][0][1]
            sent_tags.append( [ this_sent, this_label ] )
        return sent_tags 

    else :
    
        total = 0
        for elem in results :
            total += len( elem )
        print( "Total", total )
        sys.exit()
    


if __name__ == '__main__' :


    ## For eng there will be issues because of the post processing.
    # data = pickle.load( open( '../../EMNLP-2021/data/v3/en_idiom_data_v3.pk3', 'rb' ) )

    idiom_to_eval = sys.argv[1] if len( sys.argv ) > 1 else 'má-fé' 

    print( "Checking ", idiom_to_eval )
    data = pickle.load( open( '/home/harish_idioms/EMNLP-2021/data/PT/v3/pt_idiom_data_v3.pk3', 'rb' ) )
    annotation_index   = 9
    target_sent_index  = 11
    idiom_index        = 1
    changes = dict()
    verified  = False
    for train_dev_test in data.keys() :
        for idiom in data[ train_dev_test ] :
            this_idiom = idiom[0][ idiom_index ]
            if this_idiom != idiom_to_eval :
                continue
            for sent in idiom :
                sent_text = sent[ target_sent_index ]
                label     = sent[ annotation_index  ]
                db_annon = db_annotations( this_idiom )
                
                print( label ) 

                for elem in db_annon :
                    if elem[0][1].lower() == sent_text.lower() :
                        verified = True
                        if label != elem[1] :
                            if elem[1] in changes.keys() :
                                assert changes[ elem[1] ] == label
                            else :
                                changes[ elem[1] ] = label
    if verified :
        print( "All ok except, Confirm:", changes )
    else :
        print( "Could not find idiom" )
                            
