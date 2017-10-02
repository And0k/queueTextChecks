#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
  Purpose:  unit tests
  Author:   Andrey Korzh <ao.korzh@gmail.com>
  Created:  08.09.2017
"""

import unittest
from unittest.mock import patch
from sys import argv
from os import path as os_path
import datetime
from io import StringIO
import asyncio

import asyncpg

# my functions
from args import get_cfg
import textqueue

# args_for_test= argv
argv[0] = os_path.join(os_path.dirname(os_path.dirname(__file__)), __file__.strip('_'))  # .split('_')[0]
argv[1:] = []  # nose can add arguments
cfg = get_cfg()
#textqueue.cfg = cfg  # used in textqueue.insert

class MyUnit_queue(unittest.TestCase):
    """
    test api:
    add text to queue
    get task status - ready(get result)/taken/error(error description)
    """

    textqueue.task_input(queue, tube, text="test")


class MyUnit_noDB(unittest.TestCase):

    @patch('sys.stdout', new_callable=StringIO)
    def command_line_about_test(self, mock_stdout):
        """
        Check command line arguments which used to get information about program
        :param mock_stdout: set automatically by mock library
        :return:
        """
        # Display Help
        argv[1:] = ['-h']
        textqueue.main('return_cfg')
        msg_help = mock_stdout.getvalue()
        assert '--POSTGRES_DB' in msg_help

        # Check program version
        argv[1:] = ['-v']
        textqueue.main('return_cfg')
        msg_version = mock_stdout.getvalue()
        assert ' version ' in msg_version
        assert 'Andrey Korzh <ao.korzh@gmail.com>' in msg_version

        #self.cfg = cfg

class MyUnit_withDB(unittest.TestCase):
    #def setUp(self):

    ioloop = asyncio.get_event_loop()
    # Establish a connection to an existing database
    conn = ioloop.run_until_complete(
        asyncpg.connect('postgresql://postgres@localhost/' + cfg['POSTGRES_DB'],
                        user=cfg['POSTGRES_USER'], password=cfg['POSTGRES_PASSWORD']))

        # def tearDown(self):
        #     pass
    async def select(self, text_in_db):
        """
        Select a row from the table cfg[POSTGRES_TABLE] were text==text_in_db.
        :return:
        """
        global cfg
        conn= self.conn

        row = await conn.fetchrow(
            'SELECT * FROM {POSTGRES_TABLE} WHERE text = $1'.format_map(cfg), text_in_db)

        # *row* now contains
        # asyncpg.Record(id=1, name='Bob', dob=datetime.date(1984, 3, 1))
        return row


    def test_insert(self):
        # User checks some program command line arguments:
        # this dir must include instance dir with file .env:
        # argv[1:] = [] #['--POSTGRES_DB', 'test']
        # cfg = textqueue.main('return_cfg')

        global cfg
        conn= self.conn
        ioloop = self.ioloop
        textqueue.cfg = cfg  # used in textqueue.insert

        # insert some text
        time_before = datetime.datetime.now()
        test_text = 'test at {}'.format(time_before)
        ioloop.run_until_complete(textqueue.insert(conn, test_text, n_errors= 0))

        # select some data after time_before
        row= ioloop.run_until_complete(self.select(test_text))
        ioloop.close()

        time_after = datetime.datetime.now()

        # check data is correct
        assert time_after > row['t_accepted'] > time_before
        assert row['text'] == test_text
        print(row)
        """
        To check DB in pgadmin4 run it in virtualenvwrapper:
        workon queue_test
        python ~/.virtualenvs/queue_test/lib/python3.6/site-packages/pgadmin4/pgAdmin4.py
        open http://127.0.0.1:5050
        """
if __name__ == '__main__':  #
    unittest.main()  # warnings='ignore'