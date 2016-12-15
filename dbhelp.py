#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

This module provides easy methods of work with SQLite3 database.
"""

# py_ver    : [3.5.2]
# date      : [02.11.2016]
# author    : [Aleksey Yakovlev]
# email     : [nothscr@gmail.com]

import sqlite3

from time import strftime
from pathlib import Path


# file extension for database file
FILE_EXT = '.sqlite'

# Table format:
#   id      integer pk inc  - key
#   name    text            - name of text file
#   nausea  real            - value of academic nausea
#   cheat   integer         - cheat indicator
#   symbols integer         - number of symbols in raw text
#   words   integer         - number of words in text after filtering
#   uwords  integer         - number of unique words in text
TABLE_CREATE_FIELDS = """ ( id integer primary key autoincrement
                          , name text
                          , nausea real
                          , cheat integer
                          , symbols integer
                          , words integer
                          , uwords integer
                          ) """
TABLE_INSERT_FIELDS = """ ( name
                          , nausea
                          , cheat
                          , symbols
                          , words
                          , uwords
                          ) """


class SQLite3HelperError(Exception):
    """ An exception class for all errors in SQLite3Helper class-methods """
    def __init__(self, *args):
        super().__init__(args)


class TableRow(object):
    """ That class just help to build a correct tuple for insert into table """
    def __init__(self, name, nausea, cheat, symbols=-1, words=-1, uwords=-1):
        super().__init__()
        self.values = (name, nausea, cheat, symbols, words, uwords)

    def __str__(self):
        return str(self.values)


class SQLite3Helper(object):
    """ Object of this class provide an two easy methods for save data of text analisys.
        You can specify a name of database file,
        but there is an auto adding postfixes and file extension.

    :method store: accumulate data in memory, use TableRow class for correct row.
    :method flush: flushing all data from memory to database file.
    """
    def __init__(self, db_name='task'):
        super().__init__()
        self.db = {'inner': ':memory:', 'outer': self.get_filename(db_name)}

        # inner database (in memory)
        self.inner_conn = sqlite3.connect(self.db['inner'])
        self.create_structure(self.inner_conn)

        # outer database (in file)
        outer_conn = sqlite3.connect(self.db['outer'])
        self.create_structure(outer_conn)
        outer_conn.close()

    def __del__(self):
        self.inner_conn.close()

    @staticmethod
    def get_filename(filename):
        """ Build a filename for DB based on specified name, postfixes by datetime
            and version postfix if needed. Also add a file extension.
            If result filename is exist then will be added version postfix.

        :param filename: specified prefix of filename
        :return: a string that represent a name of database file
        """
        # add postfix and extension
        name_base = filename + strftime('_%y%m%d%H%M')
        file_path = Path(name_base + FILE_EXT)

        # check file exist and add version postfix if needed
        i = 0
        while file_path.exists():
            i += 1
            file_path = Path(name_base + '_{}'.format(i) + FILE_EXT)

        return file_path.name

    @staticmethod
    def create_structure(db_connection):
        """ Create a table in DB.

        :param db_connection: an object of sqlite3.Connection type
        :return: nothing awhile
        """
        curs = db_connection.cursor()

        try:
            curs.execute(""" create table textfiles {0} ; """.format(TABLE_CREATE_FIELDS))
        except:
            msg = 'Error create table for connection: {}'.format(db_connection)
            raise SQLite3HelperError(msg)

        db_connection.commit()
        curs.close()

    def store(self, values):
        """ Save a tuple of values (object of TableRow class) into memory table.

        :param values: a tuple of values (object of TableRow class) that inserting into table
        :return: nothing awhile
        """
        curs = self.inner_conn.cursor()

        try:
            curs.execute(""" insert into textfiles {0}
                                values {1} ; """.format(TABLE_INSERT_FIELDS, str(values)))
        except:
            msg = 'Error while inserting values into memory table, values = {}'.format(values)
            raise SQLite3HelperError(msg)

        self.inner_conn.commit()
        curs.close()

    def flush(self):
        """ Copy all data from inner (memory) database to outer (file) database
            and clear memory data.

        :return: nothing awhile
        """
        outer_conn = sqlite3.connect(self.db['outer'])
        outer_curs = outer_conn.cursor()
        inner_curs = self.inner_conn.cursor()

        inner_curs.execute(""" select * from textfiles order by id asc ; """)

        # transfer data from memory to database file
        row = inner_curs.fetchone()
        while row:
            try:
                outer_curs.execute(""" insert into textfiles {0}
                                          values {1} ; """.format(TABLE_INSERT_FIELDS, str(row[1:])))
            except:
                msg = """Error while inserting values into file DB
                            connection = {0}
                            values = {1}""".format(outer_conn, row)
                raise SQLite3HelperError(msg)
            row = inner_curs.fetchone()

        outer_conn.commit()
        outer_curs.close()
        outer_conn.close()

        # clear database in memory
        inner_curs.execute(""" delete from textfiles ; """)
        self.inner_conn.commit()
        inner_curs.close()


if __name__ == '__main__':
    # some test examples
    p = SQLite3Helper()
    print(p.db)
    p.store(TableRow('text1.txt', 6.6, 0))
    p.store(TableRow('text2.txt', 1.1, 1))
    p.flush()
