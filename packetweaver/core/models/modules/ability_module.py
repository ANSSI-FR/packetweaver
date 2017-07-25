import sys
import copy
import inspect
import types
import sys

import packetweaver.core.views.view_interface as view_interface
import packetweaver.core.models.abilities.ability_base as ability_base
import packetweaver.core.models.status as status
import packetweaver.core.controllers.exceptions as ex
import packetweaver.core.models.modules.module_factory
if sys.version_info > (3, 0):
    # reload moved to imp in python3
    from importlib import reload


class AbilityModule(object):

    def __init__(self, mod, mod_path, view):
        self._mod = mod
        self._mod_path = mod_path
        self._view = view
        self._defaults = {}
        self._known_opts = self._list_opts()
        self._standalone_abilities = [
            abl for abl in self._mod.exported_abilities
            if abl.get_type() == status.AbilityType.STANDALONE
        ]

    def _list_opts(self):
        s = set()
        try:
            for abl in self._mod.exported_abilities:
                s.union(set(abl.get_option_list()))
        except AttributeError:
            raise ex.Conf(
                '\nYour [{}] package does not exist or does not have a valid "exported_abilities" setup in its abilities/__init__.py module.'.format(
                    self._mod_path
                )
            )
        return s

    def set_default_options(self, opts):
        unknown_opts = [opt for opt in opts.keys() if opt not in self._known_opts]
        if len(unknown_opts) > 0:
            raise Exception('Unknown options: {}'.format(', '.join(unknown_opts)))
        self._defaults = copy.deepcopy(opts)

    def get_ability_instance_by_name(self, name, module_factory):
        # First, we reload the ability, just in case it changed on disk
        for abl in self._mod.exported_abilities:
            if abl.get_name() == name:
                reload(inspect.getmodule(abl))
        # We need to reload the "module" because the submodule were reloaded too
        self._mod = module_factory.reload_module(self._mod_path)

        for abl in self._mod.exported_abilities:
            if abl.get_name() == name:
                opts = {k: v for k, v in self._defaults.items() if k in abl.get_option_list()}
                return abl(
                    module_factory,
                    default_opts=opts,
                    view=self._view
                )
        return None

    def get_standalone_abilities(self):
        return copy.deepcopy(self._standalone_abilities)

    def get_exported_abilities(self):
        return copy.deepcopy(self._mod.exported_abilities)

    def get_option_list(self):
        return copy.deepcopy(self._known_opts)

    def get_module_path(self):
        return self._mod_path
