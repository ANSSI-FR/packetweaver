import os
import subprocess
import packetweaver.core.controllers.exceptions as ex
import packetweaver.libs.sys.path_handling as path_ha
import configparser as config_parser


class AppModel(object):
    def __init__(self, config_filename):
        """ Model to store the software configuration

        It contains main information about the software version and parses and
        serves the software configuration path (pw.ini)

        @raise os.error
        """
        self.app_version = '0.3'
        self.app_name = 'Packet Weaver'
        self.app_name_abbrev = 'pw'
        self.app_prompt_l1 = 'pw> '
        self.app_prompt_l2 = 'pw ({})> '
        self.app_slogan = 'A Python framework for ' \
                          'script filing and task sequencing'
        self.framework_path = os.getcwd()
        self._config_file = path_ha.get_abs_path(config_filename)
        self._load_config()
        self.hist_file_default_path = '.pwhistory'
        self.err_header_pkg = 'Config. file ({}) | Packages:\n'.format(
            self._config_file
        )
        self.err_header_dep = 'Config. file ({}) | Dependencies:\n'.format(
            self._config_file
        )
        self.err_header_editor = 'Config. file ({}) | Tools:\n'.format(
            self._config_file
        )
        self.err_header_hist = 'Config. file ({})| Internals:\n'.format(
            self._config_file
        )

    def _load_config(self):
        """
        @raise os.error
        """
        if not os.access(self._config_file, os.R_OK):
            raise os.error('Cannot read config file: {}'.format(
                self._config_file)
            )
        self._config = config_parser.RawConfigParser()
        self._config.read(self._config_file)

    def get_config_file_path(self):
        return self._config_file

    def get_config(self, sec, key):
        try:
            val = self._config.get(sec, key)
        except config_parser.NoOptionError:
            val = None
        except config_parser.NoSectionError:
            val = None
        return val

    def get_app_name(self):
        return self.app_name

    def get_app_version(self):
        return self.app_version

    def get_hist_file_path(self):
        """ Return a path to the file where is store the interactive CLI
            command history

        The path to this file is taken from the framework configuration file.

        :raises: ConfHistFileNotAccessible
        :returns: str containing the path to the file
        """
        hist_file_path = None
        try:
            hist_file_path = self.get_config('Internals', 'HistFile')
        except config_parser.NoSectionError:
            pass

        if hist_file_path is None:
            hist_file_path = self.hist_file_default_path
        hist_file_path = path_ha.get_abs_path(hist_file_path)

        # make sure the file exists (or create it)
        try:
            if not os.path.isfile(hist_file_path):
                open(hist_file_path, "w").close()
        except IOError:
            raise ex.ConfHistFileNotAccessible(
                '{} history file at [{}]'
                ' is not accessible or is not a file'.format(
                    self.err_header_hist, hist_file_path)
            )

        return hist_file_path

    def get_editor(self):
        """ Return the editor specified in the framework configuration file

        Having an Tools/editor configuration key is optional but must be valid
            when provided.
        The test is performed with the linux "which" command.

        :raises: ConfEditorInvalid if a specified editor is not valid
        :returns: str of the command to run the editor
                  None if no editor are specified
        """
        editor = None
        try:
            editor = self.get_config('Tools', 'editor')
            if editor is not None:
                try:
                    subprocess.check_output(['which', editor])
                except subprocess.CalledProcessError:
                    raise ex.ConfEditorInvalid(
                        '{} [{}] is not a valid editor'.format(
                            self.err_header_editor,
                            editor)
                    )
            else:
                raise ex.ConfEditorNone(
                    'No editor configured. '
                    'Please add one in your [{}] configuration file.{}'.format(
                        self.get_config_file_path(),
                        '\ne.g:\n    [Tools]\n    editor=vim'
                    )
                )
        except config_parser.NoSectionError:
            pass
        return editor

    def get_packages(self, absolute=True):
        """ Return all the pw packages path specified in the framework
            configuration file

        Tests are performed on the package paths to enforce the following
        properties:
        - this path must exists
        - it must be a folder

        The corresponding exception are raised when one of these conditions
        is not met.

        :raises: ConfPkgAbl, ConfPkgNotExists, ConfPkgNotDir, ConfPkgNone
        :returns: list of the package paths
        """
        try:
            l_pkg_path = []
            for p in self._config.options('Packages'):
                path = path_ha.get_abs_path(
                    self._config.get('Packages', p)) if absolute else p
                pkg = path[:-1] if path.endswith('/') else path
                if not os.path.exists(pkg):
                    raise ex.ConfPkgNotExists(
                        '{} - specified [{}] path does not exists'.format(
                            self.err_header_pkg, pkg)
                    )
                if not os.path.isdir(pkg):
                    raise ex.ConfPkgNotDir(
                        '{} - specified [{}] must be a directory'.format(
                            self.err_header_pkg, pkg)
                    )
                l_pkg_path.append(path)
            if len(l_pkg_path) == 0:
                raise ex.ConfPkgNone(
                    '{} - no packages are activated, you will not find '
                    'any ability.'.format(self.err_header_pkg)
                )
            return l_pkg_path
        except config_parser.NoSectionError:
            raise ex.ConfPkgNone(
                '{} - no packages are activated and '
                'the "Packages" section does not exist, '
                'you will not find any ability.'.format(self.err_header_pkg)
            )

    def get_dependencies(self):
        """ Return all dependencies specified in the framework configuration
        file.

        These dependencies are paths to python modules that are supposed
            to be added to the PYTHONPATH.
        The following tests are performed on them:

        - the path must exists
        - the path must point out a directory

        The corresponding exception are raised when one of these conditions
        is not met.

        :raises: ConfDepNotExists, ConfDepNotDir, ConfDepNone
        :returns: list of the dependency paths
        """
        try:
            l_dep = []
            for p in self._config.options('Dependencies'):
                path = self._config.get('Dependencies', p)
                if not os.path.exists(path):
                    raise ex.ConfDepNotExists(
                        '{} - specified [{}] path does not exists'.format(
                            self.err_header_dep, path)
                    )
                if not os.path.isdir(path):
                    raise ex.ConfDepNotDir(
                        '{} - specified [{}] path must point out '
                        'a python module directory'.format(
                            self.err_header_dep, path)
                    )
                l_dep.append(path)
            return l_dep
        except config_parser.NoSectionError:
            return ex.ConfDepNone()

    def get_package_name_by_path(self, path):
        """ Return a pw package corresponding to its path

        :param path: path to the package as defined in the pw.ini file
        """
        l_pkg = [
            p for p in self._config.options('Packages')
            if self._config.get('Packages', p) == path
        ]
        if len(l_pkg) == 0:
            return None
        return l_pkg[0]
