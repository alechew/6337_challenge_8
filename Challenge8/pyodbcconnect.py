import sqlite3
from sqlite3 import Error

class DataBase(object):
    """
    Class for managing database connections
    
    Methods
        get_table(table_name, where_clause) returns the result of the query select * from table_name WHERE where_clause in the form of a dictionary whose key is the first field of the result
        execute_sql(self, sql_command, nkeys=None): executes sql_command and if nkeys is a positive integer returns the results as a python dictionary whose keys are composed of the first nkeys values of each record
        update_table(self, table_name, field_name, new_value, where_clause=None) update the values in a field of a table subject to where_clause conditions
    """

    def __init__(self, db_file):
        print "Connecting to Database"
        try:
            self.con = sqlite3.connect(db_file)
        except Error as e:
            print(e)

        # Create cursor
        self.cursor = self.con.cursor()

        return

    def get_table(self, table_name, where_clause=None):
        """
        Method for turning table into python dictionary
        :param table_name: name of table
        :param where_clause: optional clause to limit rows returned.
        i.e. where_clause='COLUMN1 > 5 and COLUMN2 <= 10'
        :return: dictionary[(tuple of pks)][column_name] = value
        """

        table_data = dict()

        # Create sql command
        sql_command = "SELECT * FROM %s" % table_name
        if where_clause is not None:
            sql_command += ' WHERE ' + where_clause

        # Execute command
        self.cursor.execute(sql_command)

        # Get list of columns
        cols = [column[0] for column in self.cursor.description]

        # Convert the data to a dictionary
        for row in self.cursor.fetchall():
            table_data[row[0]] = dict(zip(cols[1:], row[1:]))

        return table_data
    
    def execute_sql(self, sql_string, nkeys=None):
        """
        Method for executing an sql command and (optionally) turning the results of an SQL query into python dictionary
        :param sql_string: sql string
        :param nkeys: 
            0 if we don't want to return anything, 
            otherwise, the first nkeys columns of the query result become the (compound, if nkeys > 1) key of the table
        :return: dictionary[(tuple of pks)][column_name] = value
        """
        
        # Execute the sql command
        self.cursor.execute(sql_string)

        if (nkeys is None) or (nkeys == 0):
            # commit and return
            self.cursor.commit()
            return
        
        # Otherwise nkeys > 0 - construct the dictionary
        table_data = dict()
        # Get list of columns
        cols = [column[0] for column in self.cursor.description] 
        
        if nkeys == 1:
            # one key, the first field of the result
            for row in self.cursor.fetchall():
                table_data[row[0]] = dict(zip(cols[1:], row[1:]))
        else:  
            # More than one key, return a dictionary with a compund key composed of the first nkeys field values
            for row in self.cursor.fetchall():
                table_data[row[0:nkeys]] = dict(zip(cols[nkeys:], row[nkeys:]))

        return table_data
    

    def update_table(self, table_name, field_name, new_value, where_clause=None):
        """
        Method for updating the values in a field of a table subject to conditions
        :param table_name: name of table
        :param field_name: name of field
        :param new_value: value to set the field to
        :param where_clause: optional clause to limit rows where the field is updated.
        i.e. where_clause='COLUMN1 > 5 and COLUMN2 <= 10'
        :return: 
        """
        # Create sql command
        sql_command = "UPDATE %s SET %s = %s" % (table_name, field_name, str(new_value))
        if where_clause is not None:
            sql_command += ' WHERE ' + where_clause

        self.cursor.execute(sql_command)
        self.cursor.commit()
        
        return
