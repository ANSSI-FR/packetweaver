# coding: utf8
import imp
import packetweaver.libs.sys.path_handling as path_ha
import packetweaver.core.models.modules.ability_module as ability_module
import packetweaver.core.views.text as output
import packetweaver.core.views.view_interface as view_interface


class ModuleFactory(object):
    """ Factory to load python modules from different types of input

    Warning : the factory does not check that modules are valid. These tests are
    hand down to the calling functions
    """

    def __init__(self, app_model, view=output.Log()):
        self._app_model = app_model
        self._view = view

    @staticmethod
    def load_module(module_path):
        """ Return the python module corresponding to the provided path

        :param module_path: path to the python module to load
        """
        return imp.load_module(module_path, None, module_path, ('', '', imp.PKG_DIRECTORY))

    reload_module = load_module

    @staticmethod
    def get_module(module_path, view=output.Log()):
        """ Return a AbilityModel based on a path

        This is mostly used to get the python module of an ability package
        :param module_path: path to the module (absolute or relative)
        :param view: a ViewsInterface subclass to handle user interface display. Needed to instantiate the ModuleModel
        """
        pkg = ModuleFactory.load_module(module_path)
        return ability_module.AbilityModule(pkg, module_path, view)

    def get_module_by_name(self, name):
        """ Retrieves a module by its name

        This is mostly use in case of ability packages, where the name
        is the one defined in the configuration file.

        The path is always returned in its absolute form.

        :param name: name of the ability package
        """
        if isinstance(self._app_model, type(None)):
            return None
        pkg_path = path_ha.get_abs_path(self._app_model.get_config('Packages', name))
        if isinstance(pkg_path, type(None)):
            return None
        return self.get_module(pkg_path, self._view)
