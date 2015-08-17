# Searches through given files and directories,
# looks for deprecated functions, and
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
# You should also note that this may produce some false positives.
#
# For anyone actually experienced in Python, I'm so sorry.

import sys

from pathutils import *
from tokenizer import Tokenizer


deprecatedDict = {
    "auto_ptr"                   : "auto_ptr is deprecated as of C++11. Consider using std::shared_ptr or std::unique_ptr.",
    "bcmp"                       : "bcmp is a POSIX legacy function, and is removed as of POSIX.1-2008. Consider using memcmp instead.",
    "bcopy"                      : "bcopy is a POSIX legacy function, and is removed as of POSIX.1-2008. Consider using memcpy instead.",
    "binary_function"            : "binary_function is deprecated as of C++11. Consider using std::function instead.",
    "binder1st"                  : "binder1st is deprecated as of C++11. Consider using std::bind instead.",
    "binder2nd"                  : "binder2nd is deprecated as of C++11. Consider using std::bind instead.",
    "bind1st"                    : "bind1st is deprecated as of C++11. Consider using std::bind instead.",
    "bind2nd"                    : "bind2nd is deprecated as of C++11. Consider using std::bind instead.",
    "bzero"                      : "bzero is a POSIX legacy function, and is removed as of POSIX.1-2008. Consider using memset instead.",
    "CLK_TCK"                    : "CLK_TCK is deprecated. Consider using CLOCKS_PER_SEC instead.",
    "const_mem_fun_t"            : "const_mem_fun_t is deprecated as of C++11.",
    "const_mem_fun1_t"           : "const_mem_fun1_t is deprecated as of C++11.",
    "const_mem_fun_ref_t"        : "const_mem_fun_ref_t is deprecated as of C++11.",
    "const_mem_fun1_ref_t"       : "const_mem_fun1_ref_t is deprecated as of C++11.",
    "ecvt"                       : "ecvt is a POSIX legacy function. Consider using std::to_string or snprintf instead.",
    "fcvt"                       : "fcvt is a POSIX legacy function. Consider using std::to_string or snprintf instead.",
    "ftime"                      : "ftime is a POSIX legacy function. Consider using functions provided by the chrono header in C++11 instead.",
    "gcvt"                       : "gcvt is a POSIX legacy function. Consider using std::to_string or snprintf instead.",
    "gethostbyaddr"              : "gethostbyaddr is deprecated in favor of getaddrinfo. Consider using it instead.",
    "gethostbyname"              : "gethostbyname is deprecated in favor of getnameinfo. Consider using it instead.",
    "get_unexpected"             : "get_unexpected is deprecated as of C++11. Consider using noexcept instead.",
    "gets"                       : "gets is removed in the C11 and C++11 standards.",
    "getwd"                      : "getwd is a POSIX legacy function. Consider using getcwd instead.",
    "inet_addr"                  : "inet_addr is a POSIX legacy function. Consider using getnameinfo or getaddrinfo instead.",
    "inet_aton"                  : "inet_aton is a POSIX legacy function. Consider using getnameinfo or getaddrinfo instead.",
    "inet_lnaof"                 : "inet_lnaof is a POSIX legacy function. Consider using getnameinfo or getaddrinfo instead.",
    "inet_makeaddr"              : "inet_makeaddr is a POSIX legacy function. Consider using getnameinfo or getaddrinfo instead.",
    "inet_netof"                 : "inet_netof is a POSIX legacy function. Consider using getnameinfo or getaddrinfo instead.",
    "inet_network"               : "inet_network is a POSIX legacy function. Consider using getnameinfo or getaddrinfo instead.",
    "inet_nsap_addr"             : "inet_nsap_addr is a POSIX legacy function. Consider using getnameinfo or getaddrinfo instead.",
    "inet_nsap_ntoa"             : "inet_nsap_ntoa is a POSIX legacy function. Consider using getnameinfo or getaddrinfo instead.",
    "inet_ntoa"                  : "inet_ntoa is a POSIX legacy function. Consider using getnameinfo or getaddrinfo instead.",
    "inet_ntop"                  : "inet_ntop is a POSIX legacy function. Consider using getnameinfo or getaddrinfo instead.",
    "inet_pton"                  : "inet_pton is a POSIX legacy function. Consider using getnameinfo or getaddrinfo instead.",
    "istrstream"                 : "istrstream is deprecated as of C++11. Consider using std::istringstream instead.",
    "mem_fun"                    : "mem_fun is deprecated as of C++11. Consider using std::mem_fn instead.",
    "mem_fun_ref"                : "mem_fun_ref is deprecated as of C++11. Consider std::mem_fn instead.",
    "mem_fun_ref_t"              : "mem_fun_ref_t is deprecated as of C++11.",
    "mem_fun1_ref_t"             : "mem_fun1_ref_t is deprecated as of C++11.",
    "mem_fun_t"                  : "mem_fun_t is deprecated as of C++11.",
    "mem_fun1_t"                 : "mem_fun1_t is deprecated as of C++11.",
    "mktemp"                     : "mktemp is a POSIX legacy function. Consider using mkstemp instead, or investigate a cross platform solution.",
    "ostrstream"                 : "ostrstream is deprecated as of C++11. Consider using std::ostringstream instead.",
    "pointer_to_binary_function" : "pointer_to_binary_function is deprecated as of C++11. Consider using std::bind or std::function instead.",
    "pointer_to_unary_function"  : "pointer_to_unary_function is deprecated as of C++11. Consider using std::bind or std::function instead.",
    "ptr_fun"                    : "ptr_fun is deprecated as of C++11. Consider using std::function or std::ref instead.",
    "random_shuffle"             : "random_shuffle is deprecated as of C++14. Consider using std::shuffle instead.",
    "set_unexpected"             : "set_unexpected is deprecated as of C++11. Consider using noexcept instead.",
    "strstream"                  : "strstream is deprecated as of C++11. Consider using std::stringstream instead.",
    "strstreambuf"               : "strstreambuf is deprecated as of C++11. Consider using std::stringstream instead.",
    "unary_function"             : "unary_function is deprecated as of C++11. Consider using std::function instead.",
    "unexpected"                 : "unexpected is deprecated as of C++11.",
    "unexpected_handler"         : "unexpected_handler is deprecated as of C++11.",
    "utimes"                     : "utimes is a POSIX legacy function. Consider using utime instead.",
    "wcswcs"                     : "wcswcs is a POSIX legacy function. Consider using wcsstr or std::wstring instead.",
}

# Defines functions that likely have better alternatives
cautionaryDict = {
    "alloca" : "alloca can be a dangerous function to use.\nIf the allocation attempt by alloca causes a stack overflow, then behavior is undefined.\nConsider using malloc, new, an STL container, or a smart pointer.",
    "itoa"   : "itoa is not a standardized library function.\nConsider using snprintf instead.",
    "rand"   : "Use of rand is not recommended. Consider using the functionality provided in the <random> header instead.",
    "scanf"  : "scanf can be a dangerous function to use.\nIt is more difficult to ensure the receiving buffer won't overflow. Consider using sscanf instead.",
    "srand"  : "Use of srand is not recommended. Consider using the functionality provided in the <random> header instead.",

    # Windows-specific functions
    "ChangeWindowMessageFilter" : "Using ChangeWindowMessageFilter is not recommended. It is recommended that ChangeWindowMessageFilterEx be used instead.",
    "GetClassInfo"              : "GetClassInfo has been superseded by GetClassInfoEx. Consider using it instead.",
    "GetClassLong"              : "GetClassLong has been superseded by GetClassLongPtr. Consider using it instead to have 32-bit and 64-bit compatible code.",
    "GetClassWord"              : "GetClassWord is a compatibility function for 16-bit versions of Windows. Strongly consider using GetClassLongPtr instead.",
    "GetWindowLong"             : "GetWindowLong has been superseded by GetWindowLongPtr. Consider using it instead to have 32-bit and 64-bit compatible code.",
    "RegisterClass"             : "RegisterClass has been superseded by RegisterClassEx. Consider using it instead.",
    "SetClassLong"              : "GetClassLong has been superseded by GetClassLongPtr. Consider using it instead to have 32-bit and 64-bit compatible code.",
    "SetClassWord"              : "SetClassWord is a compatibility function for 16-bit versions of Windows. Strongly consider using SetClassLongPtr instead.",
    "SetWindowLong"             : "SetWindowLong has been superseded by SetWindowLongPtr. Consider using it instead to have 32-bit and 64-bit compatible code.",
}


# Checks if a token contains a function name in the dictionary.
# If present, we warn the developer by printing the corresponding suggestion.
def tokenize_file(filepath):
    tokenizer = Tokenizer(filepath)
    for token in tokenizer:
        if token.string in deprecatedDict:
            print("%s: line %d - %s" % (filepath, token.linenumber, deprecatedDict[token.string]))
        if token.string in cautionaryDict:
            print("%s: line %d - %s" % (filepath, token.linenumber, cautionaryDict[token.string]))


def display_usage():
    print("Usage: deprecation-check.py <flags> [Files and directories to scan separated by spaces]\n")
    print("Flags:")
    print("\t-r - Recursively search any given directories.")


def main():
    filelist = []
    recursive_search = False

    if len(sys.argv) == 1:
        display_usage()
    else:
        for arg in sys.argv[1:]:
            if arg == "-r":
                recursive_search = True
            elif os.path.isdir(arg):
                filelist.extend(get_files_from_dir(arg, (".c", ".cc", ".cpp", ".h"), recursive_search))
            elif os.path.isfile(arg):
                filelist.append(arg)
            else:
                print("Invalid argument specified: %s" % arg)
                display_usage()
                return
        for file in filelist:
            tokenize_file(file)


# TODO/NOTE/Whatever: Is there a better way than doing this that doesn't require external libs?
if __name__ == "__main__":
    main()
