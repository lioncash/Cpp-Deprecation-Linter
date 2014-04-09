import os


# Gets source files from a given directory that match any of the extensions passed in.
def get_files_from_dir(directory, extensions, recursive):
    files = []
    for root, dirnames, filenames in os.walk(directory, topdown=True):
        for file in filenames:
            if file.endswith(extensions):
                files.append(os.path.join(root, file))

        if not recursive:
            break

    return files