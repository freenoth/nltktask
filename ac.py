#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

This module represent logic of detection and conversion of cheats.
"""

# py_ver    : [3.5.2]
# date      : [02.11.2016]
# author    : [Aleksey Yakovlev]
# email     : [nothscr@gmail.com]


class AntiCheater(object):
    """ Help to detect and convert text cheats.

    :method check_word: convert word if needed and indicate cheating
    """
    def __init__(self):
        super().__init__()

        self.LRUS = set('АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя')
        self.LENG = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')

        self.TR_URUS = list('АВЕКМНОРСТУХЬ')
        self.TR_UENG = list('ABEKMHOPCTYXb')

        self.TR_LRUS = list('аеикорсухь')
        self.TR_LENG = list('aeukopcyxb')

    def check_word(self, word):
        """ Check word for creats - changing russian letters by similar english and vice versa.
            Detect cheats and converts cheat-letters to source language.

        :param word: a word to check
        :return: a tuple like (result_word, is_cheat)
            is_cheat = 0 - there is no cheats or 'word' is not alphabetic
                result_word = source word

            is_cheat = 1 - cheat found
                result_word = source word with cheat correction

            is_cheat = -1 - cheats maybe found, all letters can be both of rus and eng
                if number of RUS unique letters less than ENG, then
                    result_word = source word with translate to ENG
                else
                    result_word = source word with translate to RUS

            is_cheat = -2 - there is bot of rus and eng letters, but it can convert to another lang
                result_word = source word
        """
        is_cheat = 0
        result_word = word

        if not word.isalpha():
            return result_word, is_cheat

        # get set of letters by language
        rus_parts = {x for x in word if (x in self.LRUS)}
        eng_parts = {x for x in word if (x in self.LENG)}

        if not rus_parts or not eng_parts:
            # if only one language detected - there is no cheats
            return result_word, is_cheat

        # check letters can be converted to another language
        check_rus = rus_parts.issubset(set(self.TR_LRUS + self.TR_URUS))
        check_eng = eng_parts.issubset(set(self.TR_LENG + self.TR_UENG))

        if not check_rus and not check_eng:
            # strange word, but..
            is_cheat = -2

        elif check_rus and not check_eng:
            # translate to english
            is_cheat = 1
            result_word = word.translate(str.maketrans(''.join(self.TR_LRUS + self.TR_URUS),
                                                       ''.join(self.TR_LENG + self.TR_UENG)))

        elif not check_rus and check_eng:
            # translate to russian
            is_cheat = 1
            result_word = word.translate(str.maketrans(''.join(self.TR_LENG + self.TR_UENG),
                                                       ''.join(self.TR_LRUS + self.TR_URUS)))

        else:
            is_cheat = -1

            if len(rus_parts) >= len(eng_parts):
                # translate to russian
                result_word = word.translate(str.maketrans(''.join(self.TR_LENG + self.TR_UENG),
                                                           ''.join(self.TR_LRUS + self.TR_URUS)))
            else:
                # translate to english
                result_word = word.translate(str.maketrans(''.join(self.TR_LRUS + self.TR_URUS),
                                                           ''.join(self.TR_LENG + self.TR_UENG)))

        return result_word, is_cheat


def _main():
    police = AntiCheater()

    print(police.check_word('мoлoкo'))
    print(police.check_word('milk'))
    print(police.check_word('ёжuк'))
    print(police.check_word('cмecb'))
    print(police.check_word('вecтник'))
    print(police.check_word('КНИГА'))
    print(police.check_word('кyкушка'))
    print(police.check_word('kykaреку'))
    print(police.check_word('АВТOMOБИЛb'))
    print(police.check_word('superДОМ'))


if __name__ == '__main__':
    _main()
