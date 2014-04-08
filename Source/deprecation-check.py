# Searches through directories from a given base directory
# and looks through C/C++ files for deprecated functions and
# suggests alternatives.
#
# This script assumes that the codebase being examined is not
# limited from using C++11 functions, etc.
#
# Further note that this script does not in anyway attempt to determine
# if the function name refers the deprecated function in the standard library
# or if it's part of your actual codebase. However, you shouldn't be declaring
# functions with the same name as ones in the standard library within your
# codebase, because that's just a plain bad idea in the first place. Couple
# it with 'using namespace std;' and you also get pretty nifty™ clashing possibilities.
#
# Further the further note by noting that this will likely produce quite a bit of false positives, as
# this doesn't even lex or tokenize the files. This may or may not change in the future.
#
# For anyone actually experienced in Python, I'm so sorry.

import os
import sys

from exceptions import ParseException
from exceptions import PEBCAKException
from tokenizer import Token


deprecatedFuncDict = {
	"auto_ptr"                   : "auto_ptr is deprecated as of C++11. Consider using shared_ptr or unique_ptr.",
	"binary_function"            : "binary_function is deprecated as of C++11.",
	"binder1st"                  : "binder1st is deprecated as of C++11. Consider using std::bind instead.",
	"binder2nd"                  : "binder2nd is deprecated as of C++11. Consider using std::bind instead.",
	"bind1st"                    : "bind1st is deprecated as of C++11. Consider using std::bind instead.",
	"bind2nd"                    : "bind2nd is deprecated as of C++11. Consider using std::bind instead.",
	"const_mem_fun_t"            : "const_mem_fun_t is deprecated as of C++11.",
	"const_mem_fun1_t"           : "const_mem_fun1_t is deprecated as of C++11.",
	"const_mem_fun_ref_t"        : "const_mem_fun_ref_t is deprecated as of C++11.",
	"const_mem_fun1_ref_t"       : "const_mem_fun1_ref_t is deprecated as of C++11.",
	"get_unexpected"             : "get_unexpected is deprecated as of C++11.",
	"gets"                       : "gets is removed in the C11 and C++11 standards.",
	"istrstream"                 : "istrstream is deprecated as of C++11.",
	"mem_fun"                    : "mem_fun is deprecated as of C++11. Consider using std::mem_fn instead.",
	"mem_fun_ref"                : "mem_fun_ref is deprecated as of C++11. Consider using std::bind or std::function instead.",
	"mem_fun_ref_t"              : "mem_fun_ref_t is deprecated as of C++11.",
	"mem_fun1_ref_t"             : "mem_fun1_ref_t is deprecated as of C++11.",
	"mem_fun_t"                  : "mem_fun_t is deprecated as of C++11.",
	"mem_fun1_t"                 : "mem_fun1_t is deprecated as of C++11.",
	"ostrstream"                 : "ostrstream is deprecated as of C++11.",
	"pointer_to_binary_function" : "pointer_to_binary_function is deprecated as of C++11.",
	"pointer_to_unary_function"  : "pointer_to_unary_function is deprecated as of C++11.",
	"ptr_fun"                    : "ptr_fun is deprecated as of C++11. Consider using std::function or std::ref instead.",
	"set_unexpected"             : "set_unexpected is deprecated as of C++11.",
	"strstream"                  : "strstream is deprecated as of C++11.",
	"strstreambuf"               : "strstreambuf is deprecated as of C++11.",
	"unary_function"             : "unary_function is deprecated as of C++11.",
	"unexpected"                 : "unexpected is deprecated as of C++11.",
	"unexpected_handler"         : "unexpected_handler is deprecated as of C++11.",
}

# TODO
# This dictionary will be part of a feature that can
# caution a dev depending on certain functions (ie. strcpy vs. strncpy, etc).
cautionaryFuncDict = {
}


# Read the file and returns sanitized lines in the form of tokens.
def readFile(filepath):
	tokens = []
	with open(filepath) as sourceFile:
		for i, line in enumerate(sourceFile):
			if "/*" in line:
				if line.count("/*") > 1:
					raise ParseException("Error in file %s at line %d. Starting a multi-line comment in an existing multi-line comment is not valid in C/C++." % (filepath, i+1))

				# Swallow characters until we hit the end of the comment.
				while "*/" not in line and line != "":
					line = sourceFile.readline()
					if "/*" in line:
						raise ParseException("Error in file %s at line %d. Starting a multi-line comment in an existing multi-line comment is not valid in C/C++." % (filepath, i+1))

				temp = line.split("*/", 1)[1]
				if temp:
					tokens.append(Token(i, temp))
			elif "//" in line:
				temp = line.split("//", 1)[0]
				if temp:
					tokens.append(Token(i, temp))
			else:
				if not line.isspace():
					tokens.append(Token(i, line))
	return tokens

# Checks if a token contains a function name in the dictionary.
# If present, we warn the developer by printing the corresponding suggestion.
def parseTokens(filename, tokens):
	for token in tokens:
		for key in deprecatedFuncDict:
			if key in token.string:
				print("%s: line %d - %s" % (filename, token.lineNumber+1, deprecatedFuncDict[key]))

def parseFile(filepath):
	tokens = readFile(filepath)
	parseTokens(filepath, tokens)

# Determines the files to parse
def determineFiles(baseDirectory):
	for root, dirs, files in os.walk(baseDirectory, topdown=True):
		for name in files:
			filePath = os.path.join(root, name)
			if filePath.endswith((".c", ".cc",".cpp", ".h")):
				parseFile(filePath)

def main():
	if len(sys.argv) > 1:
		baseDir = sys.argv[1]

		if os.path.exists(baseDir):
			determineFiles(baseDir)
		else:
			raise PEBCAKException("Specified top directory does not exist. Terminating...")
	else:
		print("Usage: deprecation-check.py [directory to read files in]")

# TODO/NOTE/Whatever: Is there a better way than doing this that doesn't require external libs?
if __name__ == "__main__":
	main()
