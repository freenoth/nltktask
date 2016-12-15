#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

A little bit of tests using pytest module.
"""

# py_ver    : [3.5.2]
# date      : [02.11.2016]
# author    : [Aleksey Yakovlev]
# email     : [nothscr@gmail.com]

import ac


POLICE = ac.AntiCheater()


class TestAntiCheat(object):
    def test_base_word(self):
        assert POLICE.check_word('test') == ('test', 0)

    def test_not_word(self):
        assert POLICE.check_word('not word 123') == ('not word 123', 0)

    def test_rus_letter_in_eng(self):
        assert POLICE.check_word('tеst') == ('test', 1)

    def test_eng_letter_in_rus(self):
        assert POLICE.check_word('тeст') == ('тест', 1)

    def test_both_not_convert(self):
        assert POLICE.check_word('мылоqwe') == ('мылоqwe', -2)

    def test_both_convert_to_rus(self):
        assert POLICE.check_word('ааoo') == ('ааоо', -1)

    def test_both_convert_to_eng(self):
        assert POLICE.check_word('ааyoo') == ('aayoo', -1)
