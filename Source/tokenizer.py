# TODO: Improve this greatly.

from exceptions import ParseException


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
        self.filepath = filepath
        self._tokenlist = []
        self._tokenIdx = 0
        self._parse_file(filepath)

    def __str__(self):
        return "Tokenizer - %s" % self.filepath

    def __repr__(self):
        return "Tokenizer - %s" % self.filepath

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

    def _peek(self, file, num):
        pos = file.tell()
        data = file.read(num)
        file.seek(pos, 0)
        return data

    # Reads through a multi-line comment and returns the number of lines
    def _handle_multi_line_comment(self, file, linenumber):
        line = file.readline()
        linenumber += 1
        if line == "":
            raise ParseException("Expected closing specifier for multi-line comment, got EOF instead.")

        while "*/" not in line:
            if "/*" in line:
                raise ParseException("Error in file %s at line %d - Multi-line comments cannot be nested within other multi-line comments in C/C++." % (file, linenumber))
            elif line == "":
                raise ParseException("Error in file %s at line %d - Expected closing specifier for multi-line comment, got EOF instead." % (file, linenumber))
            else:
                line = file.readline()
                linenumber += 1

        # Handle the case where some dingus might put code right after the terminator.
        splitstr = line.split("*/")[1]
        if len(splitstr) > 0:
            for s in splitstr.split(" "):
                self._tokenlist.append(Token(linenumber, s.strip()))

        return linenumber

    def _parse_file(self, filepath):
        with open(filepath) as sourcefile:
            linenum = 1
            linechar = sourcefile.read(1)
            tokenstr = ""

            while linechar != "":
                if linechar == "/" and self._peek(sourcefile, 1) == '/':
                    sourcefile.readline()
                    linenum += 1
                elif linechar == "/" and self._peek(sourcefile, 1) == "*":
                    linenum += self._handle_multi_line_comment(sourcefile, linenum)
                else:
                    # TODO: Improve this, tokenizing by spaces is likely not correct
                    #       since we don't tokenize parentheses in certain cases, etc.
                    if linechar == ' ':
                        self._tokenlist.append(Token(linenum, tokenstr))
                        tokenstr = ""
                    else:
                        tokenstr += linechar

                linechar = sourcefile.read(1)