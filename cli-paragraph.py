# -*- coding: utf-8 -*-
import sys
import textwrap
import unicodedata
from itertools import groupby

import re
import argparse

#copy from docutils
east_asian_widths = {'W': 2,   # Wide
                     'F': 2,   # Full-width (wide)
                     'Na': 1,  # Narrow
                     'H': 1,   # Half-width (narrow)
                     'N': 1,   # Neutral (not East Asian, treated as narrow)
                     'A': 1}   # Ambiguous (s/b wide in East Asian context,
                               # narrow otherwise, but that doesn't work)

#copy from docutils
def column_width(text):
    """Return the column width of text.

    Correct ``len(text)`` for wide East Asian and combining Unicode chars.
    """
    if isinstance(text, str) and sys.version_info < (3,0):
        return len(text)
    combining_correction = sum([-1 for c in text
                                if unicodedata.combining(c)])
    try:
        width = sum([east_asian_widths[unicodedata.east_asian_width(c)]
                     for c in text])
    except AttributeError:  # east_asian_width() New in version 2.4.
        width = len(text)
    return width + combining_correction


class TextWrapper(textwrap.TextWrapper):
    """Custom subclass that uses a different word splitter."""

    def _wrap_chunks(self, chunks):
        """_wrap_chunks(chunks : [string]) -> [string]

        Original _wrap_chunks use len() to calculate width.
        This method respect to wide/fullwidth characters for width adjustment.
        """
        lines = []
        if self.width <= 0:
            raise ValueError("invalid width %r (must be > 0)" % self.width)

        chunks.reverse()

        while chunks:
            cur_line = []
            cur_len = 0

            if lines:
                indent = self.subsequent_indent
            else:
                indent = self.initial_indent

            width = self.width - column_width(indent)

            if self.drop_whitespace and chunks[-1].strip() == '' and lines:
                del chunks[-1]

            while chunks:
                l = column_width(chunks[-1])

                if cur_len + l <= width:
                    cur_line.append(chunks.pop())
                    cur_len += l

                else:
                    break

            if chunks and column_width(chunks[-1]) > width:
                self._handle_long_word(chunks, cur_line, cur_len, width)

            if self.drop_whitespace and cur_line and cur_line[-1].strip() == '':
                del cur_line[-1]

            if cur_line:
                lines.append(indent + ''.join(cur_line))

        return lines

    def _break_word(self, word, space_left):
        """_break_word(word : string, space_left : int) -> (string, string)

        Break line by unicode width instead of len(word).
        """
        total = 0
        for i,c in enumerate(word):
            total += column_width(c)
            if total > space_left:
                return word[:i-1], word[i-1:]
        return word, ''

    def _split(self, text):
        """_split(text : string) -> [string]

        Override original method that only split by 'wordsep_re'.
        This '_split' split wide-characters into chunk by one character.
        """
        split = lambda t: textwrap.TextWrapper._split(self, t)
        chunks = []
        for chunk in split(text):
            for w, g in groupby(chunk, column_width):
                if w == 1:
                    chunks.extend(split(''.join(g)))
                else:
                    chunks.extend(list(g))
        return chunks

    def _handle_long_word(self, reversed_chunks, cur_line, cur_len, width):
        """_handle_long_word(chunks : [string],
                             cur_line : [string],
                             cur_len : int, width : int)

        Override original method for using self._break_word() instead of slice.
        """
        space_left = max(width - cur_len, 1)
        if self.break_long_words:
            l, r = self._break_word(reversed_chunks[-1], space_left)
            cur_line.append(l)
            reversed_chunks[-1] = r

        elif not cur_line:
            cur_line.append(reversed_chunks.pop())


MAXWIDTH = 70


def fw_wrap(text, width=MAXWIDTH, **kwargs):
    w = TextWrapper(width=width, **kwargs)
    return w.wrap(text)

parser = argparse.ArgumentParser(
    description='テキストファイルをLaTeXの段落のように整形し、単一の改行は無視して連続した改行で段落下げを行う'
)

parser.add_argument('-s', '--space', type=str, default='  '        , help='字下げに使用する空白文字。デフォルト値は半角スペース2個。')
parser.add_argument('-w', '--width', type=int, default=80          , help='最大幅。デフォルトは80。')
parser.add_argument('input_file'   , type=str, default='/dev/stdin', help='入力ファイル。')

input_str = open(parser.parse_args().input_file).read()
output_str = re.sub(r'([^\n])\n($|[^\n])', r'\1\2', input_str) # 2つ以上連続しない改行を削除
output_str = re.sub(r'^\n+', r''  , output_str)                # ファイル先頭の1つ以上連続する改行を削除
output_str = re.sub(r'\n*$', r''  , output_str)                # ファイル末尾の1つ以上連続する改行を削除
output_str = re.sub(r'\n+' , r'\n', output_str)                # 2つ以上連続する改行を1つの改行に置換

for splitted_output_str in output_str.split('\n'):
    for line in fw_wrap(parser.parse_args().space + splitted_output_str, parser.parse_args().width):
        print(line)
