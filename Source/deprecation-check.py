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
# it with 'using namespace std;' and you also get pretty nifty clashing possibilities.
#
# Further the further note by noting that this will likely produce quite a bit of false positives, as
# this doesn't even lex or tokenize the files. This may or may not change in the future.
#
# For anyone actually experienced in Python, I'm so sorry.

import os
import sys

from exceptions import PEBCAKException
from tokenizer import Tokenizer


deprecatedFuncDict = {
    "auto_ptr"                   : "auto_ptr is deprecated as of C++11. Consider using shared_ptr or unique_ptr.",
    "bcmp"                       : "bcmp is a POSIX standard function, and is removed as of POSIX.1-2008. Consider using memcmp instead.",
    "bcopy"                      : "bcopy is a POSIX standard function, and is removed as of POSIX.1-2008. Consider using memcpy instead.",
    "binary_function"            : "binary_function is deprecated as of C++11.",
    "binder1st"                  : "binder1st is deprecated as of C++11. Consider using std::bind instead.",
    "binder2nd"                  : "binder2nd is deprecated as of C++11. Consider using std::bind instead.",
    "bind1st"                    : "bind1st is deprecated as of C++11. Consider using std::bind instead.",
    "bind2nd"                    : "bind2nd is deprecated as of C++11. Consider using std::bind instead.",
    "bzero"                      : "bzero is a POSIX standard function, and is removed as of POSIX.1-2008. Consider using memset instead.",
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
    "alloca" : "alloca can be a dangerous function to use.\nIf the allocation attempt by alloca causes a stack overflow, then behavior is undefined.\nConsider using malloc or new.",

   # Windows-specific functions
   "ChangeWindowMessageFilter" : "Using ChangeWindowMessageFilter is not recommended. It is recommended that ChangeWindowMessageFilterEx be used instead.",
   "GetClassInfo"              : "GetClassInfo has been superseded by GetClassInfoEx. Consider using it instead.",
   "GetClassLong"              : "GetClassLong has been superseded by GetClassLongPtr. Consider using it instead to have 32-bit and 64-bit compatible code.",
   "GetWindowLong"             : "GetWindowLong has been superseded by GetWindowLongPtr. Consider using it instead to have 32-bit and 64-bit compatible code.",
   "RegisterClass"             : "RegisterClass has been superseded by RegisterClassEx. Consider using it instead.",
   "SetClassLong"              : "GetClassLong has been superseded by GetClassLongPtr. Consider using it instead to have 32-bit and 64-bit compatible code.",
   "SetWindowLong"             : "SetWindowLong has been superseded by SetWindowLongPtr. Consider using it instead to have 32-bit and 64-bit compatible code.",
}


# Checks if a token contains a function name in the dictionary.
# If present, we warn the developer by printing the corresponding suggestion.
def evaluate_tokens(tokenizer):
    for token in tokenizer:
        for key in deprecatedFuncDict:
            if key in token.string:
                print("%s: line %d - %s" % (tokenizer.filepath, token.linenumber + 1, deprecatedFuncDict[key]))
                break
        for key in cautionaryFuncDict:
            if key in token.string:
                print("%s: line %d - %s" % (tokenizer.filepath, token.linenumber + 1, cautionaryFuncDict[key]))
                break


def tokenize_file(filepath):
    tokenizer = Tokenizer(filepath)
    evaluate_tokens(tokenizer)


# Determines the files to parse
def determine_files(basedirectory):
    for root, dirs, files in os.walk(basedirectory, topdown=True):
        for name in files:
            filepath = os.path.join(root, name)
            if filepath.endswith((".c", ".cc", ".cpp", ".h")):
                tokenize_file(filepath)


def main():
    if len(sys.argv) > 1:
        basedir = sys.argv[1]

        if os.path.exists(basedir):
            determine_files(basedir)
        else:
            raise PEBCAKException("Specified top directory does not exist. Terminating...")
    else:
        print("Usage: deprecation-check.py [directory to read files in]")

# TODO/NOTE/Whatever: Is there a better way than doing this that doesn't require external libs?
if __name__ == "__main__":
    main()
