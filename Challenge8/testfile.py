import sqlite3
from sqlite3 import Error

database = "Challenge8.db"


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return None


def displayDataForLane(tableName):

    # create a database connection
    conn = create_connection(database)

    cur = conn.cursor()
    cur.execute("SELECT * FROM " + tableName)
    
    rows = cur.fetchall()
    
    for row in rows:
        print(row)


create_connection(database)
main()