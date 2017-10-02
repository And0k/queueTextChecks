#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
  Purpose:  funtional test
  Author:   Andrey Korzh <ao.korzh@gmail.com>
  Created:  08.09.2017
"""
from io import StringIO
import unittest
from unittest.mock import patch
from sys import argv
from os import path as os_path

from textqueue import main

# args_for_test= argv
argv[0] = os_path.join(os_path.dirname(os_path.dirname(__file__)), __file__.strip('_')) #.split('_')[0]

class MyUnitTests(unittest.TestCase):
    # def setUp(self):
    #     pass
    # def tearDown(self):
    #     pass

    def test_insert(self):
        # User checks some program command line arguments:
        # this dir must include instance dir with file .env:
        global argv
        return
        argv[1:] = ['--POSTGRES_DB', 'test']
        cfg = main('return_cfg')

        #argv= args_for_test
        # It finds all test files and parse them. Result saved to
        #d:\Work\_Python3\And0K\scraper3\scrxPDF\test\result\10209_PROD GAS+_(N).csv
        #log saved to

@patch('sys.stdout', new_callable=StringIO)
def command_line_about_test(mock_stdout):
    """
    Check command line arguments which used to get information about program
    :param mock_stdout: set automatically by mock library
    :return:
    """
    # Display Help
    argv[1:] = ['-h']
    cfg= main('return_cfg')
    msg_help= mock_stdout.getvalue()
    assert '--POSTGRES_DB' in msg_help

    # Check program version
    argv[1:] = ['-v']
    cfg= main('return_cfg')
    msg_version= mock_stdout.getvalue()
    assert ' version ' in msg_version
    assert 'Andrey Korzh <ao.korzh@gmail.com>' in msg_version


if __name__ == '__main__':  #
    unittest.main() #warnings='ignore'