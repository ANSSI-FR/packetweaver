import os


def get_abs_path(path_, ref=None):
    """ Return an absolute path

     It handles the following formats:

     * ~/things
     * ../things
     * things
     * /path/to/things

     :param path_: path
     :param ref: reference path to handle relative paths
     :return: absolute path
     """
    path = path_
    if path_.startswith('~'):
        path = os.path.expanduser(path_)
    elif not path_.startswith('/'):
        if ref is not None:
            prevdir = os.getcwd()
            try:
                os.chdir(ref)
                path = os.path.abspath(path_)
            finally:
                os.chdir(prevdir)
        else:
            path = os.path.abspath(path_)

    return path[:-1] if path.endswith('/') else path
