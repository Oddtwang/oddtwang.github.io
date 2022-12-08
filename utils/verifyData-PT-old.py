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



def db_annotations( idiom, table ) : 

    query    = "select * from idioms where idiom = '" + idiom + "' ;"
    results  = list( reversed( mysql_obj.mysql_get( query ) ) )
    
    idiom_id = int( results[0][0] )
    query    = "SELECT data FROM " + table + " WHERE idiom_id = " + str( idiom_id ) + ";"
    results  = list( reversed( mysql_obj.mysql_get( query ) ) )

    
    assert len( results ) > 0
    
    results  = results[-1][0]
    
    results  = re.sub( r'^\'', '', results )
    results  = re.sub( r'\'$', '', results )
    
    results = json.loads( results )

    if table == 'annotations_p2' or table == 'annotations_p3' : 

        print( "Total", len( results[ 'annotations' ] ) )

    
        annotations = results[ 'annotations' ]
        meanings    = results[ 'meanings'    ]
        sentences   = results[ 'sentences'   ]

        sent_tags = list()
        for index in range( len( sentences ) ) :
            this_sent  = sentences[ index ][ 'data' ][1]
            this_label = [ i for i in meanings if i[0] == int( annotations[ index ] ) ][0][1]
            sent_tags.append( [ this_sent, label ] )
        return sent_tags 

    else :
    
        total = 0
        for elem in results :
            total += len( elem )
        print( "Total", total )
        sys.exit()
    


if __name__ == '__main__' :


    ## For eng there will be issues because of the post processing.
    # table = 'annotations_p3' 
    # data = pickle.load( open( '../../EMNLP-2021/data/v3/en_idiom_data_v3.pk3', 'rb' ) )
    table = 'annotations_p2' 
    data = pickle.load( open( 'pt_idiom_data_v3.pk3', 'rb' ) )
    annotation_index   = 9
    target_sent_index  = 11
    idiom_index        = 1
    for train_dev_test in data.keys() :
        for idiom in data[ train_dev_test ] :
            this_idiom = idiom[0][ idiom_index ]
            for sent in idiom :
                sent_text = sent[ target_sent_index ]
                label     = sent[ annotation_index  ]

                db_annon = db_annotations( this_idiom, table )

                found = False
                for elem in db_annon :
                    if elem[0].lower() == sent_text.lower() :
                        assert label == elem[1]
                        found = True
                        break
                if not found :
                    print( sent_text, "not found" ) 
    print( "All match" ) 
