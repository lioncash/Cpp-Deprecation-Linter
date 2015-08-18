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

import argparse

from pathutils import *
from tokenizer import Tokenizer

# C/C++ standard library
deprecatedDict = {
    "auto_ptr"                   : "auto_ptr is deprecated as of C++11. Consider using std::shared_ptr or std::unique_ptr.",
    "binary_function"            : "binary_function is deprecated as of C++11. Consider using std::function instead.",
    "binder1st"                  : "binder1st is deprecated as of C++11. Consider using std::bind instead.",
    "binder2nd"                  : "binder2nd is deprecated as of C++11. Consider using std::bind instead.",
    "bind1st"                    : "bind1st is deprecated as of C++11. Consider using std::bind instead.",
    "bind2nd"                    : "bind2nd is deprecated as of C++11. Consider using std::bind instead.",
    "CLK_TCK"                    : "CLK_TCK is deprecated. Consider using CLOCKS_PER_SEC instead.",
    "const_mem_fun_t"            : "const_mem_fun_t is deprecated as of C++11.",
    "const_mem_fun1_t"           : "const_mem_fun1_t is deprecated as of C++11.",
    "const_mem_fun_ref_t"        : "const_mem_fun_ref_t is deprecated as of C++11.",
    "const_mem_fun1_ref_t"       : "const_mem_fun1_ref_t is deprecated as of C++11.",
    "get_unexpected"             : "get_unexpected is deprecated as of C++11. Consider using noexcept instead.",
    "gets"                       : "gets is removed in the C11 and C++11 standards.",
    "istrstream"                 : "istrstream is deprecated as of C++11. Consider using std::istringstream instead.",
    "mem_fun"                    : "mem_fun is deprecated as of C++11. Consider using std::mem_fn instead.",
    "mem_fun_ref"                : "mem_fun_ref is deprecated as of C++11. Consider std::mem_fn instead.",
    "mem_fun_ref_t"              : "mem_fun_ref_t is deprecated as of C++11.",
    "mem_fun1_ref_t"             : "mem_fun1_ref_t is deprecated as of C++11.",
    "mem_fun_t"                  : "mem_fun_t is deprecated as of C++11.",
    "mem_fun1_t"                 : "mem_fun1_t is deprecated as of C++11.",
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
}

# Functions that likely have better alternatives
cautionaryDict = {
    "alloca" : "alloca can be a dangerous function to use.\nIf the allocation attempt by alloca causes a stack overflow, then behavior is undefined.\nConsider using malloc, new, an STL container, or a smart pointer.",
    "itoa"   : "itoa is not a standardized library function.\nConsider using snprintf instead.",
    "rand"   : "Use of rand is not recommended. Consider using the functionality provided in the <random> header instead.",
    "scanf"  : "scanf can be a dangerous function to use.\nIt is more difficult to ensure the receiving buffer won't overflow. Consider using sscanf instead.",
    "srand"  : "Use of srand is not recommended. Consider using the functionality provided in the <random> header instead.",
}

# POSIX API-related warnings
posixDict = {
    "bcmp"                      : "bcmp is a POSIX legacy function, and is removed as of POSIX.1-2008. Consider using memcmp instead.",
    "bcopy"                     : "bcopy is a POSIX legacy function, and is removed as of POSIX.1-2008. Consider using memcpy instead.",
    "bzero"                     : "bzero is a POSIX legacy function, and is removed as of POSIX.1-2008. Consider using memset instead.",
    "cuserid"                   : "cuserid is a POSIX legacy function and is removed as of POSIX.1-2001. Consider replacing it with getpwuid(geteuid()).",
    "ecvt"                      : "ecvt is a POSIX legacy function. Consider using std::to_string or snprintf instead.",
    "fcvt"                      : "fcvt is a POSIX legacy function. Consider using std::to_string or snprintf instead.",
    "ftime"                     : "ftime is a POSIX legacy function. Consider using functions provided by the chrono header in C++11 instead.",
    "gcvt"                      : "gcvt is a POSIX legacy function. Consider using std::to_string or snprintf instead.",
    "gethostbyaddr"             : "gethostbyaddr has been obsoleted in POSIX 1003.1. Consider using getaddrinfo instead.",
    "gethostbyname"             : "gethostbyname has been obsoleted in POSIX 1003.1. Consider using getnameinfo instead.",
    "getwd"                     : "getwd is a POSIX legacy function. Consider using getcwd instead.",
    "inet_addr"                 : "inet_addr is a POSIX legacy function. Consider using getnameinfo or getaddrinfo instead.",
    "inet_aton"                 : "inet_aton is a POSIX legacy function. Consider using getnameinfo or getaddrinfo instead.",
    "inet_lnaof"                : "inet_lnaof is a POSIX legacy function. Consider using getnameinfo or getaddrinfo instead.",
    "inet_makeaddr"             : "inet_makeaddr is a POSIX legacy function. Consider using getnameinfo or getaddrinfo instead.",
    "inet_netof"                : "inet_netof is a POSIX legacy function. Consider using getnameinfo or getaddrinfo instead.",
    "inet_network"              : "inet_network is a POSIX legacy function. Consider using getnameinfo or getaddrinfo instead.",
    "inet_nsap_addr"            : "inet_nsap_addr is a POSIX legacy function. Consider using getnameinfo or getaddrinfo instead.",
    "inet_nsap_ntoa"            : "inet_nsap_ntoa is a POSIX legacy function. Consider using getnameinfo or getaddrinfo instead.",
    "inet_ntoa"                 : "inet_ntoa is a POSIX legacy function. Consider using getnameinfo or getaddrinfo instead.",
    "inet_ntop"                 : "inet_ntop is a POSIX legacy function. Consider using getnameinfo or getaddrinfo instead.",
    "inet_pton"                 : "inet_pton is a POSIX legacy function. Consider using getnameinfo or getaddrinfo instead.",
    "mktemp"                    : "mktemp is a POSIX legacy function. Consider using mkstemp instead, or investigate a cross platform solution.",
    "utimes"                    : "utimes is a POSIX legacy function. Consider using utime instead.",
    "wcswcs"                    : "wcswcs is a POSIX legacy function. Consider using wcsstr or std::wstring instead.",
}

# Windows API-related warnings
windowsDict = {
    "AddMRUStringW"                      : "AddMRUStringW is deprecated as of Windows Vista.",
    "AppendMenuWrapW"                    : "AppendMenuWrapW should not be used. Consider using AppendMenuW instead.",
    "CallCPLEntry16"                     : "CallCPLEntry16 is removed as of Windows Vista.",
    "CallWindowProcWrapW"                : "CallWindowProcWrapW should not be used. Consider using CallWindowProcW instead.",
    "CanShareFolderW"                    : "CanShareFolderW is deprecated as of Windows Vista.",
    "ChangeWindowMessageFilter"          : "Using ChangeWindowMessageFilter is not recommended. It is recommended that ChangeWindowMessageFilterEx be used instead.",
    "CharLowerWrapW"                     : "CharLowerWrapW should not be used. Consider using CharLowerW instead.",
    "CharUpperWrapW"                     : "CharUpperWrapW should not be used. Consider using CharUpperW instead.",
    "CharUpperBuffWrapW"                 : "CharUpperBuffWrapW should not be used. Consider using CharUpperBuff instead.",
    "CIDLData_CreateFromIDArray"         : "CIDLData_CreateFromIDArray is removed as of Windows Vista.",
    "CompareStringWrapW"                 : "CompareStringWrapW should not be used. Consider using CompareStringEx instead.",
    "CopyFileWrapW"                      : "CopyFileWrapW should not be used. Consider using CopyFile instead.",
    "ConnectToConnectionPoint"           : "ConnectToConnectionPoint is deprecated as of Windows Vista.",
    "CreateEventWrapW"                   : "CreateEventWrapW should not be used. Consider using CreateEvent or CreateEventEx instead.",
    "CreateFileWrapW"                    : "CreateFileWrapW should not be used. Consider using CreateFile instead.",
    "CreateHardwareMoniker"              : "CreateHardwareMoniker is deprecated as of Windows Vista.",
    "CreateUserProfileEx"                : "CreateUserProfileEx has been removed in Windows Vista.",
    "CreateWindowExWrapW"                : "CreateWindowExWrapW should not be used. Consider using CreateWindowEx instead.",
    "CscSearchApiGetInterface"           : "CscSearchApiGetInterface is deprecated as of Windows 7.",
    "DAD_AutoScroll"                     : "DAD_AutoScroll is deprecated as of Windows Vista.",
    "DAD_DragEnterEx"                    : "DAD_DragEnterEx is deprecated as of Windows Vista. Consider using ImageList_DragEnter instead.",
    "DAD_DragEnterEx2"                   : "DAD_DragEnterEx2 is deprecated as of Windows Vista. Consider using ImageList_DragEnter instead.",
    "DAD_DragLeave"                      : "DAD_DragLeave is deprecated as of Windows Vista. Consider using ImageList_DragLeave instead.",
    "DAD_DragMove"                       : "DAD_DragMove is deprecated as of Windows Vista. Consider using ImageList_DragMove instead.",
    "DAD_SetDragImage"                   : "DAD_SetDragImage is deprecated as of Windows Vista. Consider using ImageList_BeginDrag instead.",
    "DAD_ShowDragImage"                  : "DAD_ShowDragImage is deprecated as of Windows Vista. Consider using ImageList_DragShowNoLock instead.",
    "DoEnvironmentSubst"                 : "DoEnvironmentSubst is deprecated as of Windows Vista. Consider using ExpandEnvironmentStrings instead.",
    "DefWindowProcWrapW"                 : "DefWindowProcWrapW should not be used. Consider using DefWindowProc instead.",
    "DeleteFileWrapW"                    : "DeleteFileWrapW should not be used. Consider using DeleteFile instead.",
    "DialogBoxParamWrapW "               : "DialogBoxParamWrapW should not be used. Consider using DialogBoxParam instead.",
    "DispatchMessageWrapW"               : "DispatchMessage should not be used. Consider using DispatchMessage instead.",
    "DragQueryFileWrapW"                 : "DragQueryFileWrapW should not be used. Consider using DragQueryFile instead.",
    "DrawTextExWrapW"                    : "DrawTextExWrapW should not be used. Consider using DrawTextEx instead.",
    "DrawTextWrapW"                      : "DrawTextWrapW should not be used. Consider using DrawText instead.",
    "DriveType"                          : "DriveType is deprecated as of Windows Vista. Consider using GetDriveType in the Volume Management API instead.",
    "EnumMRUListW"                       : "EnumMRUListW is deprecated as of Windows Vista.",
    "EstimateFileRisk"                   : "EstimateFileRisk is deprecated as of Windows Vista. IAttachmentExecute should be used instead.",
    "ExtractAssociatedIconEx"            : "ExtractAssociatedEx is deprecated.",
    "ExtTextOutWrapW"                    : "ExtTextOutWrapW should not be used. Consider using ExtTextOut instead.",
    "FindResourceWrapW"                  : "FindResourceWrapW should not be used. Consider using FindResourceW instead.",
    "FormatMessageWrapW"                 : "FormatMessageWrapW should not be used. Consider using FormatMessage instead.",
    "GetClassInfo"                       : "GetClassInfo has been superseded by GetClassInfoEx. Consider using it instead.",
    "GetClassInfoWrapW"                  : "GetClassInfoWrapW should not be used. Consider using GetClassInfoEx instead.",
    "GetClassLong"                       : "GetClassLong has been superseded by GetClassLongPtr. Consider using it instead to have 32-bit and 64-bit compatible code.",
    "GetClassWord"                       : "GetClassWord is a compatibility function for 16-bit versions of Windows. Strongly consider using GetClassLongPtr instead.",
    "GetDateFormatWrapW"                 : "GetDateFormatWrapW should not be used. Consider using GetDateFormatEx instead.",
    "GetDlgItemTextWrapW"                : "GetDlgItemTextWrapW should not be used. Consider using GetDlgItemTextWrapW instead.",
    "GetFileAttributesWrapW"             : "GetFileAttributesWrapW should not be used. Consider using GetFileAttributes or GetFileAttributesEx instead.",
    "GetFileNameFromBrowse"              : "GetFileNameFromBrowse is deprecated as of Windows Vista.",
    "GetLocaleInfoWrapW"                 : "GetLocaleWrapW should not be used. Consider using GetLocalInfoEx instead.",
    "GetMenuItemInfoWrapW"               : "GetMenuItemInfoWrapW should not be used. Consider using GetMenuItemInfo instead",
    "GetMenuPosFromID"                   : "GetMenuPosFromID is deprecated.",
    "GetModuleFileNameWrapW"             : "GetModuleFileNameWrapW should not be used. Consider using GetModuleFileName or GetModuleFileNameEx instead.",
    "GetModuleHandleWrapW"               : "GetModuleHandleWrapW should not be used. Consider using GetModuleHandle or GetModuleHandleEx instead.",
    "GetObjectWrapW"                     : "GetObjectWrapW should not be used. Consider using GetObject instead.",
    "GetOpenFileName"                    : "GetOpenFileName has been superseded by the Common Item Dialog in Windows Vista. Consider using it instead.",
    "GetOpenFileNameWrapW"               : "GetOpenFileNameWrapW should not be used. Consider using the Common Item Dialog instead.",
    "GetSaveFileName"                    : "GetSaveFileName has been superseded by the Common Item Dialog in Windows Vista. Consider using it instead.",
    "GetSaveFileNameWrapW"               : "GetSaveFileNameWrapW should not be used. Consider using the Common Item Dialog instead.",
    "GetSystemDirectoryWrapW"            : "GetSystemDirectoryWrapW should not be used. Consider using GetSystemDirectory instead.",
    "GetTimeFormatWrapW"                 : "GetTimeFormatWrapW should not be used. Consider using GetTimeFormatW instead.",
    "GetVersionEx"                       : "GetVersionEx is deprecated as of Windows 8.1. Consider using the Version Helper API functions instead.",
    "GetWindowLong"                      : "GetWindowLong has been superseded by GetWindowLongPtr. Consider using it instead to have 32-bit and 64-bit compatible code.",
    "GetWindowLongWrapW"                 : "GetWindowLongWrapW should not be used. Consider using GetWindowLong, or GetWindowLongPtr if a handle is being retrieved.",
    "GetWindowsDirectoryWrapW"           : "GetWindowsDirectoryWrapW should not be used. Consider using GetWindowsDirectory instead.",
    "GetWindowTextLengthWrapW"           : "GetWindowTextLengthWrapW should not be used. Consider using GetWindowTextLength instead.",
    "GetWindowTextWrapW"                 : "GetWindowTextWrapW should not be used. Consider using GetWindowText instead.",
    "GUIDFromString"                     : "GUIDFromString has been deprecated as of Windows Vista. Consider using CLSIDFromString or IIDFromString instead.",
    "ILLoadFromStream"                   : "ILLoadFromStream is deprecated as of Windows Vista.",
    "InsertMenuItemWrapW"                : "InsertMenuItemWrapW should not be used. Consider using InsertMenuItem instead.",
    "IsCharAlphaWrapW"                   : "IsCharAlphaWrapW should not be used. Consider using IsCharAlpha instead.",
    "IsCharAlphaNumericWrapW"            : "IsCharAlphaNumericWrapW should not be used. Consider using IsCharAlphaNumeric instead.",
    "IsCharUpperWrapW"                   : "IsCharUpperWrapW should not be used. Consider using IsCharUpper instead.",
    "IsNetDrive"                         : "IsNetDrive is deprecated as of Windows Vista. Consider using GetDriveType in the Volume Management API, or WNetGetConnection in the Networking API instead.",
    "IsUserAnAdmin"                      : "IsUserAnAdmin is deprecated as of Windows Vista.",
    "LinkWindow_RegisterClass"           : "LinkWindow_Register class is deprecated as of Windows Vista. Consider using InitCommonControlsEx instead.",
    "LinkWindow_UnregisterClass"         : "LinkWindow_Register class is deprecated as of Windows Vista.",
    "LoadLibraryWrapW"                   : "LoadLibraryWrapW should not be used. Consider using LoadLibrary or LoadLibraryEx instead.",
    "LoadStringWrapW"                    : "LoadStringWrapW should not be used. Consider using LoadString instead.",
    "MessageBoxWrapW"                    : "MessageBoxWrapW should not be used. Consider using MessageBox instead.",
    "MoveFileWrapW"                      : "MoveFileWrapW should not be used. Consider using MoveFile, MoveFileEx, MoveFileWithProgress, or MoveFileTransacted instead.",
    "MLFreeLibrary"                      : "MLFreeLibrary is removed as of Windows 7.",
    "MLHtmlHelp"                         : "MLHtmlHelp is deprecated as of Windows Vista.",
    "MLLoadLibrary"                      : "MLLoadLibrary is removed as of Windows 7.",
    "MLWinHelp"                          : "MLWinHelp is deprecated as of Windows Vista.",
    "OpenRegStream"                      : "OpenRegStream is deprecated as of Windows Vista. Consider using SHOpenRegStream2 instead.",
    "OutputDebugStringWrapW"             : "OutputDebugStringWrapW is deprecated as of Windows Vista. Consider using OutputDebugStringW instead.",
    "PassportWizardRunDll"               : "PassportWizardRunDll is deprecated as of Windows Vista.",
    "PathCleanupSpec"                    : "PathCleanupSpec is deprecated as of Windows Vista.",
    "PathGetShortPath"                   : "PathGetShortPath is deprecated as of Windows Vista.",
    "PathIsExe"                          : "PathIsExe is deprecated as of Windows Vista.",
    "PathIsSlow"                         : "PathIsSlow is deprecated as of Windows Vista.",
    "PathProcessCommand"                 : "PathProcessCommand is deprecated as of Windows Vista.",
    "PathResolve"                        : "PathResolve is deprecated as of Windows Vista.",
    "PeekMessageWrapW"                   : "PeekMessageWrapW should not be used. Consider using PeekMessage instead.",
    "PerUserInit"                        : "PerUserInit is deprecated as of Windows Vista.",
    "PickIconDlg"                        : "PickIconDlg is deprecated as of Windows Vista.",
    "PostMessageWrapW"                   : "PostMessageWrapW should not be used. Consider PostMessage or PostThreadMessage instead.",
    "ReadCabinetState"                   : "ReadCabinetState is deprecated as of Windows Vista.",
    "RealDriveType"                      : "RealDriveType is deprecated as of Windows Vista. Consider using GetDriveType in the Volume Management API instead.",
    "RegCreateKeyExWrapW"                : "RegCreateKeyExWrapW should not be used. Consider using RegCreateKeyEx or RegCreateKeyTransacted instead.",
    "RegisterClass"                      : "RegisterClass has been superseded by RegisterClassEx. Consider using it instead.",
    "RegisterClassWrapW"                 : "RegisterClassWrapW should not be used. Consider using RegisterClassEx instead.",
    "RegOpenKeyExWrapW"                  : "RegOpenKeyExWrapW should not be used. Consider using RegOpenKeyEx or RegOpenKeyTransacted instead.",
    "RegQueryValue"                      : "RegQueryValue has been superseded by RegQueryValueEx. Consider using it instead.",
    "RegQueryValueExWrapW"               : "RegQueryValueExWrapW should not be used. Consider using RegQueryValueEx instead.",
    "RegSetValueExWrapW"                 : "RegSetValueExWrapW should not be used. Consider using RegSetValueEx instead.",
    "RestartDialog"                      : "RestartDialog is deprecated in Windows Vista. Consider using ExitWindowsEx instead.",
    "RestartDialogEx"                    : "RestartDialogEx is deprecated in Windows Vista. Consider using ExitWindowsEx instead.",
    "SendMessageWrapW"                   : "SendMessageWrapW should not be used. Consider using SendMessage instead.",
    "SetClassLong"                       : "GetClassLong has been superseded by GetClassLongPtr. Consider using it instead to have 32-bit and 64-bit compatible code.",
    "SetClassWord"                       : "SetClassWord is a compatibility function for 16-bit versions of Windows. Strongly consider using SetClassLongPtr instead.",
    "SetDlgItemTextWrapW"                : "SetDlgItemTextWrapW should not be used. Consider using SetDlgItemText instead.",
    "SetWindowLong"                      : "SetWindowLong has been superseded by SetWindowLongPtr. Consider using it instead to have 32-bit and 64-bit compatible code.",
    "SetWindowLongWrapW"                 : "SetWindowLongWrapW should not be used. Consider using SetWindowLong, or SetWindowLongPtr if a handle is being set instead.",
    "SetWindowTextWrapW"                 : "SetWindowTextWrapW should not be used. Consider using SetWindowText instead.",
    "ShellExecuteExWrapW"                : "ShellExecuteExWrapW should not be used. Consider using ShellExecuteEx instead.",
    "ShellMessageBoxWrapW"               : "ShellMessageBoxWrapW should not be used. Consider using ShellMessageBox instead.",
    "SHAddFromPropSheetExtArray"         : "SHAddFromPropSheetExtArray is deprecated as of Windows Vista.",
    "SHAlloc"                            : "SHAlloc is deprecated as of Windows Vista. Consider using CoTaskMemAllocInstead,",
    "SHAllocShared"                      : "SHAllocShared is deprecated as of Windows Vista.",
    "SHAnsiToAnsi"                       : "SHAnsiToAnsi is deprecated as of Windows Vista.",
    "SHAnsiToUnicode"                    : "SHAnsiToUnicode is deprecated as of Windows Vista.",
    "SHCloneSpecialIDList"               : "SHCloneSpecialIDList is deprecated as of Windows Vista. Consider using SHGetSpecialFolderLocation instead.",
    "SHCLSIDFromString"                  : "SHCLSIDFromString is deprecated as of Windows Vista. Consider using CLSIDFromString instead.",
    "SHCoCreateInstance"                 : "SHCoCreateInstance is deprecated as of Windows Vista. Consider using CoCreateInstanceInstead.",
    "SHCreateDirectory"                  : "SHCreateDirectory is deprecated as of Windows Vista.",
    "SHCreateDirectoryEx"                : "SHCreateDirectoryEx is deprecated as of Windows Vista.",
    "SHCreateFileExtractIcon"            : "SHCreateFileExtractIcon is deprecated as of Windows Vista.",
    "SHCreateProcessAsUserW"             : "SHCreateProcessAsUserW is removed as of Windows Vista.",
    "SHCreatePropSheetExtArray"          : "SHCreatePropSheetExtArray is deprecated as of Windows Vista.",
    "SHCreateQueryCancelAutoPlayMoniker" : "SHCreateQueryCancelAutoPlayMoniker is deprecated as of Windows Vista. Consider using CreateClassMoniker instead.",
    "SHCreateStdEnumFmtEtc"              : "SHCreateStdEnumFmtEtc is deprecated as of Windows Vista.",
    "SHCreateStreamOnFile"               : "SHCreateStreamOnFile is deprecated as of Windows Vista. Consider using SHCreateStreamOnFileEx.",
    "SHDestroyPropSheetExtArray"         : "SHDestroyPropSheetExtArray is deprecated as of Windows Vista.",
    "Shell_GetCachedImageIndex"          : "Shell_GetCachedImageIndex is deprecated as of Windows Vista. Consider using Shell_GetCachedImageIndexA or Shell_GetCachedImageIndexW instead.",
    "Shell_GetImageLists"                : "Shell_GetImageLists is deprecated as of Windows Vista.",
    "Shell_MergeMenus"                   : "Shell_MergeMenus is deprecated as of Windows Vista.",
    "ShellMessageBox"                    : "ShellMessageBox is deprecated as of Windows Vista.",
    "SHExtractIconsW"                    : "SHExtractIconsW is deprecated as of Windows Vista.",
    "SHFind_InitMenuPopup"               : "SHFind_InitMenuPopup is deprecated as of Windows Vista.",
    "SHFindFiles"                        : "SHFindFiles is deprecated as of Windows Vista.",
    "SHFlushClipboard"                   : "SHFlushClipboard is removed in Windows Vista. Consider using OleFlushClipboard instead.",
    "SHFlushSFCache"                     : "SHFlushSFCache is deprecated as of Windows Vista.",
    "SHFormatDateTime"                   : "SHFormatDateTime is deprecated as of Windows Vista.",
    "SHFormatDrive"                      : "SHFormatDrive is deprecated as of Windows Vista.",
    "SHFree"                             : "SHFree is deprecated as of Windows Vista. Consider using CoTaskMemFree instead.",
    "SHFreeShared"                       : "SHFreeShared is deprecated as of Windows Vista.",
    "SHGetAttributesFromDataObject"      : "SHGetAttributesFromDataObject is deprecated as of Windows Vista.",
    "SHGetFileInfoWrapW"                 : "SHGetFileInfoWrapW should not be used. Consider using SHGetFileInfo instead.",
    "SHGetFolderLocation"                : "SHGetFolderLoacation is deprecated as of Windows Vista. Consider using SHGetKnownFolderIDList instead.",
    "SHGetFolderPath"                    : "SHGetFolderPath is deprecated as of Windows Vista. Consider using SHGetKnownFolderPath instead.",
    "SHGetFolderPathAndSubDir"           : "SHGetFolderPathAndSubDir is deprecated as of Windows Vista.",
    "SHGetInverseCMAP"                   : "SHGetInverseCMAP is deprecated as of Windows Vista.",
    "SHGetMalloc"                        : "SHGetMalloc is deprecated as of Windows Vista. Consider using CoTaskMemAlloc instead.",
    "SHGetPathFromIDListWrapW"           : "SHGetPathFromIDListWrapW should not be used. Consider using SHGetPathFromIDList instead.",
    "SHGetRealIDL"                       : "SHGetRealIDL is deprecated as of Windows Vista.",
    "SHGetSetFolderCustomSettings"       : "SHGetSetFolderCustomSettings is deprecated as of Windows Vista.",
    "SHGetSetSettings"                   : "SHGetSetSettings is deprecated as of Windows Vista.",
    "SHGetShellStyleHInstance"           : "SHGetShellStyleHInstance is removed in Windows Vista and later.",
    "SHGetSpecialFolderLocation"         : "SHGetSpecialFolderLocation is deprecated as of Windows 2000. Consider using SHGetKnownFolderIDList instead.",
    "SHGetSpecialFolderPath"             : "SHGetSpecialFolderPath is deprecated as of Windows 2000. Consider using SHGetKnownFolderPath instead.",
    "SHGetViewStatePropertyBag"          : "SHGetViewStatePropertyBag is deprecated as of Windows Vista.",
    "SHHandleUpdateImage"                : "SHHandleUpdateImage is deprecated as of Windows Vista.",
    "SHILCreateFromPath"                 : "SHILCreateFromPath is deprecated as of Windows Vista. Consider using SHParseDisplayName instead.",
    "SHInvokePrinterCommand"             : "SHInvokePrinterCommand is deprecated as of Windows Vista. It is recommended to invoke verbs on printers via IContextMenu or ShellExecute.",
    "SHIsChildOrSelf"                    : "SHIsChildOrSelf is deprecated as of Windows Vista.",
    "SHLimitInputEdit"                   : "SHLimitInputEdit is deprecated as of Windows Vista.",
    "SHLoadOLE"                          : "SHLoadOLE is deprecated as of Windows Vista.",
    "SHLockShared"                       : "SHLockShared is deprecated as of Windows Vista.",
    "SHMapIDListToImageListIndexAsync"   : "SHMapIDListToImageListIndexAsync is removed in Windows Vista.",
    "SHMapPIDLToSystemImageListIndex"    : "SHMapPIDLToSystemImageListIndex is deprecated as of Windows Vista.",
    "SHMessageBoxCheck"                  : "SHMessageBoxCheck is deprecated as of Windows Vista.",
    "SHObjectProperties"                 : "SHObjectProperties is deprecated as of Windows Vista.",
    "SHOpenPropSheet"                    : "SHOpenPropSheet is deprecated as of Windows Vista.",
    "SHOpenRegStream"                    : "SHOpenRegStream has been superseded by SHOpenRegStream2. Consider using it instead.",
    "SHRegGetBoolValueFromHKCUHKLM"      : "SHRegGetBoolValueFromHKCUHKLM is deprecated as of Windows Vista.",
    "SHRegGetValue"                      : "SHRegGetValue is deprecated as of Windows Vista. Consider using RegGetValue instead.",
    "SHRegGetValueFromHKCUHKLM"          : "SHRegGetValueFromHKCUHKLM is deprecated as of Windows Vista.",
    "SHReplaceFromPropSheetExtArray"     : "SHReplaceFromPropSheetExtArray is deprecated as of Windows Vista.",
    "SHRestricted"                       : "SHRestricted is deprecated as of Windows Vista.",
    "SHSetFolderPath"                    : "SHSetFolderPath is deprecated as of Windows Vista. Consider using SHSetKnownFolderPath instead.",
    "SHSendMessageBroadcast"             : "SHSendMessageBroadcast is deprecated as of Windows Vista. Consider using SendMessage with the hWnd parameter as HWND_BROADCAST instead.",
    "SHShellFolderView_Message"          : "SHShellFolderView_Message is deprecated as of Windows Vista.",
    "SHSimpleIDListFromPath"             : "SHSimpleIDListFromPath is deprecated as of Windows 8. Consider the following alternatives: \n\t1. Call SHGetDesktopFolder to obtain IShellFolder for the desktop folder.\n\t2. Get the IShellFolder's bind context (IBindCtx).\n\t3. Call IShellFolder::ParseDisplayName with the IBindCtx and the path.",
    "SHStartNetConnectionDialog"         : "SHStartNetConnectionDialog is deprecated as of Windows Vista.",
    "SHStripMneumonic"                   : "SHStripMneumonic is deprecated as of Windows Vista.",
    "SHUnicodeToAnsi"                    : "SHUnicodeToAnsi is deprecated as of Windows Vista.",
    "SHUnicodeToUnicode"                 : "SHUnicodeToUnicode is deprecated as of Windows Vista.",
    "SHUnlockShared"                     : "SHUnlockShared is deprecated as of Windows Vista.",
    "SHValidateUNC"                      : "SHValidateUNC is deprecated as of Windows 7.",
    "SignalFileOpen"                     : "SignalFileOpen is deprecated as of Windows Vista.",
    "StopWatchFlush"                     : "StopWatchFlush is deprecated as of Windows Vista.",
    "StopWatchMode"                      : "StopWatchMode is deprecated as of Windows Vista.",
    "TranslateAcceleratorWrapW"          : "TranslateAcceleratorWrapW should not be used. Consider using TranslateAccelerator instead.",
    "UnregisterClassWrapW"               : "UnregisterClassWrapW should not be used. Consider using UnregisterClass instead.",
    "UpdateAllDesktopSubscriptions"      : "UpdateAllDesktopSubscriptions is deprecated",
    "UrlFixupW"                          : "UrlFixupW is deprecated as of Windows 8",
    "WhichPlatform"                      : "WhichPlatform is deprecated as of Windows Vista",
    "Win32DeleteFile"                    : "Win32DeleteFile is deprecated as of Windows Vista",
    "WOWShellExecute"                    : "WOWShellExecute is deprecated as of Windows Vista. Consider using ShellExecute instead.",
    "WriteCabinetState"                  : "WriteCabinetState is deprecated as of Windows Vista."
}


# Checks if a token contains a function name in the dictionary.
# If present, we warn the developer by printing the corresponding suggestion.
def tokenize_file(filepath, cautionary, posix, windows):
    tokenizer = Tokenizer(filepath)
    for token in tokenizer:
        if token.string in deprecatedDict:
            print("%s: line %d - %s" % (filepath, token.linenumber, deprecatedDict[token.string]))
        if cautionary and token.string in cautionaryDict:
            print("%s: line %d - %s" % (filepath, token.linenumber, cautionaryDict[token.string]))
        if posix and token.string in posixDict:
            print("%s: line %d - %s" % (filepath, token.linenumber, posixDict[token.string]))
        if windows and token.string in windowsDict:
            print("%s: line %d - %s" % (filepath, token.linenumber, windowsDict[token.string]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--recursive", action="store_true", help="recursive file search")
    parser.add_argument("-i", "--inputs", nargs="*", help="directories or files to check separated by spaces")
    parser.add_argument("--cautionary", action="store_true", help="warn about functions that may have better alternatives")
    parser.add_argument("--posix", action="store_true", help="warn about certain POSIX API functions")
    parser.add_argument("--windows", action="store_true", help="warn about certain Windows API functions")

    args = parser.parse_args()

    # TODO: Let the user specify the extensions to search by.
    extensions = (".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx", ".tpp")
    filelist = []
    for file in args.inputs:
        if os.path.isdir(file):
            filelist.extend(get_files_from_dir(file, extensions, args.recursive))
        elif os.path.isfile(file):
            filelist.append(file)

    for file in filelist:
        tokenize_file(file, args.cautionary, args.posix, args.windows)


if __name__ == "__main__":
    main()
