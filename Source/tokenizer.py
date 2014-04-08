# TODO: Improve this greatly.

from exceptions import ParseException

class Token:
	def __init__(self, lineNumber, string):
		self.lineNumber = lineNumber
		self.string = string

	def __str__(self):
		return self.string

	def __repr__(self):
		return self.string


class Tokenizer:
	def __init__(self, filepath):
		self.filepath = filepath
		self.__tokenlist = []
		self.__tokenIdx = 0
		self.__parseFile(filepath)

	def __str__(self):
		return "Tokenizer - %s" % self.filepath

	def __repr__(self):
		return "Tokenizer - %s" % self.filepath

	def __iter__(self):
		self.__tokenIdx = 0
		return self

	def __next__(self):
		if self.__tokenIdx >= len(self.__tokenlist):
			raise StopIteration
		else:
			token = self.__tokenlist[self.__tokenIdx]
			self.__tokenIdx += 1
			return token

	def _peek(self, file, num):
		pos = file.tell()
		data = file.read(num)
		file.seek(pos, 0)
		return data

	# Reads through a multi-line comment and returns the number of lines
	def _handleMultiLineComment(self, file, linenumber):
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
		splitStr = line.split("*/")[1]
		if len(splitStr) > 0:
			for s in splitStr.split(" "):
				self.__tokenlist.append(Token(linenumber, s.strip()))

		return linenumber

	def __parseFile(self, filepath):
		with open(filepath) as sourcefile:
			linenum = 1
			lineCh = sourcefile.read(1)
			tokenStr = ""

			while lineCh != "":
				if lineCh == "/" and self._peek(sourcefile, 1) == '/':
					sourcefile.readline()
					linenum += 1
				elif lineCh == "/" and self._peek(sourcefile, 1) == "*":
					linenum += self._handleMultiLineComment(sourcefile, linenum)

				# TODO: Improve this, tokenizing by spaces is likely not correct
				#       since we don't tokenize parentheses, etc.
				if lineCh == ' ':
					self.__tokenlist.append(Token(linenum, tokenStr))
					tokenStr = ""
				else:
					tokenStr += lineCh

				lineCh = sourcefile.read(1)