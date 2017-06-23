# coding: utf8
# for future python 3 compatibility
import os
import sys
import packetweaver.libs.sys.path_handling as path_ha
if sys.version_info > (3, 0):
    import configparser as config_parser
else:
    import ConfigParser as config_parser


class AppModel(object):
    def __init__(self, config_filename):
        """ Model to store the software configuration

        It contains main information about the software version and parses and
        serves the software configuration path (pw.ini)

        @raise os.error
        """
        self.app_version = "0.1"
        self.app_name = "Packet Weaver"
        self.app_name_abbrev = "pw"
        self.app_prompt_l1 = "pw> "
        self.app_prompt_l2 = "pw ({})> "
        self.app_slogan = "A Python framework for script filing and task sequencing"
        self.framework_path = os.getcwd()
        self._load_config(config_filename)

    def _load_config(self, config_filename):
        """
        @raise os.error
        """
        self._config_file = config_filename
        if not os.access(self._config_file, os.R_OK):
            raise os.error('Cannot read config file: {}'.format(self._config_file))
        self._config = config_parser.RawConfigParser()
        self._config.read(self._config_file)

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

    def get_packages(self, absolute=True):
        """ Return all the pw packages path of the activated packages

        return only absolute

        :returns: list of the paths
        """
        try:
            if absolute is True:
                return [path_ha.get_abs_path(self._config.get('Packages', p)) for p in self._config.options('Packages')]
            return [self._config.get('Packages', p) for p in self._config.options('Packages')]
        except config_parser.NoSectionError:
            return []

    def get_dependencies(self):
        """ Return all the pw packages path of the activated packages

        :returns: list of the paths
        """
        try:
            return [self._config.get('Dependencies', p) for p in self._config.options('Dependencies')]
        except config_parser.NoSectionError:
            return []

    def get_package_name_by_path(self, path):
        """ Return a pw package corresponding to its path

        :param path: path to the package as defined in the pw.ini file
        """
        l = [
            p
            for p in self._config.options('Packages')
            if self._config.get('Packages', p) == path
        ]
        if len(l) == 0:
            return None
        return l[0]
