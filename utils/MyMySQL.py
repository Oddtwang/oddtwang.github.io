import os
import mysql.connector


class MyMySQL : 

    ## Update with DB details here. 
    mysql_connection = None
    username         = 'idiom'
    database         = 'idioms'
    host             = 'mysql.idioms.harishtayyarmadabushi.com' 

    def __init__( self, config_path="./", database=None, username=None, password=None, host=None ) : 
        
        if database is None : 
            database = self.database
        if username is None : 
            username = self.username
        if password is None : 
            password = open( os.path.join( config_path, '.db-details' ) ).read().lstrip().rstrip()

        if host     is None : 
            host     = self.host

        connection = mysql.connector.connect( 
            user      =  username    , 
            password  =  password    ,
            host      =  host        ,
            database  =  database
        )

        

        self.mysql_connection = connection

    def __del__( self ) : 

        try: 
            self.mysql_connection.close()
        except: 
            # Might have been destroyed already!
            pass 
        return 1

    def mysql_do( self, command ) : 

        cursor = self.mysql_connection.cursor()
        cursor.execute( 'SET NAMES utf8' )
        cursor.execute( command )
        cursor.close()

        self.mysql_connection.commit()

        return 1


    def mysql_insert( self, command, iterator ) : 

        cursor = self.mysql_connection.cursor()
        cursor.execute( 'SET NAMES utf8' )
        cursor.executemany( command, iterator )

        cursor.close()

        self.mysql_connection.commit()

        return 1

    def mysql_insert_one( self, command, data ) : 

        cursor = self.mysql_connection.cursor()
        cursor.execute( 'SET NAMES utf8' )
        cursor.execute( command, data )

        cursor.close()

        self.mysql_connection.commit()

        return 1

    def mysql_get( self, command ) : 
        
        cursor = self.mysql_connection.cursor()
        cursor.execute( 'SET NAMES utf8' )
        cursor.execute( command )

        results = list()
        for elem in cursor : 
            results.append( elem ) 

        cursor.close()

        return list( reversed( results ) )
        



if __name__ == "__main__":

    tmp = MyMySQL()
    print( tmp.mysql_get( "select * from idioms" ) )
