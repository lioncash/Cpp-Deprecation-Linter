# TODO: Improve this greatly.
# TODO: Skip tokenizing string occurrences. These are not necessary.

import re


class Token:
    def __init__(self, linenumber, string):
        self.linenumber = linenumber
        self.string = string

    def __str__(self):
        return self.string

    def __repr__(self):
        return self.string


class Tokenizer:
    def __init__(self, filepath):
        self._filepath = filepath
        self._tokenlist = []
        self._tokenIdx = 0
        self._parse_file(filepath)

    def __str__(self):
        return "Tokenizer - %s" % self._filepath

    def __repr__(self):
        return "Tokenizer - %s" % self._filepath

    def __iter__(self):
        self._tokenIdx = 0
        return self

    def __next__(self):
        if self._tokenIdx >= len(self._tokenlist):
            raise StopIteration
        else:
            token = self._tokenlist[self._tokenIdx]
            self._tokenIdx += 1
            return token

    def _peek(self, file, num=1):
        pos = file.tell()
        data = file.read(num)
        file.seek(pos, 0)
        return data

    # TODO: This is really crappy sanitizing. We should be able to parse with these present;
    #       however, this is only necessary if we want to do small static analysis checks in the future.
    def _sanitize_add_token(self, linenum, string):
        santized_string = re.sub("<[^>]*>", "", string)  # Clip off templated arguments if possible.
        santized_string = re.sub("[()!+-/*~^#?:><&|;{}]", " ", santized_string)  # Now remove other unnecessary characters
        split_list = santized_string.split(" ")
        for item in split_list:
            if item:
                self._tokenlist.append(Token(linenum, item))

    def _parse_file(self, filepath):
        with open(filepath) as sourcefile:
            in_multi_line_comment = False
            in_string = False
            linenum = 1
            linechar = sourcefile.read(1)
            tokenstr = ""

            while linechar != "":
                if linechar == "\n":
                    linenum += 1

                if not in_multi_line_comment and not in_string:
                    if linechar == "/" and self._peek(sourcefile) == '/':
                        sourcefile.readline()
                        linenum += 1
                    elif linechar == "/" and self._peek(sourcefile) == "*":
                        in_multi_line_comment = True
                    elif linechar == "\"":
                        in_string = True
                    elif linechar == "'":
                        if self._peek(sourcefile) == "\\":  # Special character escapes
                            sourcefile.read(3)
                        else:
                            sourcefile.read(2)
                    elif linechar.isspace() and not tokenstr.isspace():
                        self._sanitize_add_token(linenum, tokenstr)
                        tokenstr = ""  # New token
                    else:
                        tokenstr += linechar
                elif in_multi_line_comment and linechar == "*" and self._peek(sourcefile) == "/":
                    in_multi_line_comment = False
                    sourcefile.read(1)
                elif in_string:
                    if linechar == "\\":   # Skip escaped chars
                        sourcefile.read(1)
                    elif linechar == "\"":
                        in_string = False

                linechar = sourcefile.read(1)