import re
import os
import sys
import json

base_path  = '../'
utils_path = os.path.join( os.path.dirname( os.path.realpath(__file__) ), base_path + "utils")
sys.path.append( utils_path )

from MyMySQL                import MyMySQL
mysql_obj = MyMySQL(config_path=utils_path)


idiom_id = 276
query    = "SELECT data FROM annotations_p2 WHERE idiom_id = " + str( idiom_id ) + " and user_id = 1;"
results  = list( reversed( mysql_obj.mysql_get( query ) ) )

assert len( results ) == 1

results  = results[0][0]

results  = re.sub( r'^\'', '', results )
results  = re.sub( r'\'$', '', results )

results = json.loads( results ) 

annotations = results[ 'annotations' ]
meanings    = results[ 'meanings'    ]
sentences   = results[ 'sentences'   ]

assert len( annotations ) == len( sentences )

meanings_dict = dict()
for meaning in meanings :
    meanings_dict[ meaning[0] ] = meaning[1]

for i in range( len( annotations ) ) :
    print( sentences[i][ 'data' ][1], "-->", meanings_dict[ int( annotations[ i ] ) ] )
    print()

print( annotations ) 
