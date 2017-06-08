# coding: utf8
import abc
import copy
import packetweaver.core.models.modules.module_factory as module_factory
import packetweaver.core.models.abilities.ability_base as ability_base
import packetweaver.core.views.view_interface as view_interface
import packetweaver.core.views.text as output


class ModuleListModel(object):

    def __init__(self, paths, view=output.Log()):
        """ The model used to interact with the list of available modules

        Note: module is the model used to interact with the real ability. See ModuleModel

        :param paths: list of paths to the activated ability packages
        :param view: a ViewInterface subclass to handle user interface display
        """
        self._paths = copy.deepcopy(paths)
        self._view = view
        self._module_list = {}
        self.reload()

    def reload(self):
        self._module_list.clear()
        self._last_search_results = []
        self._ability_name_words = set()
        self._ability_tags = set()

        self._refresh_module_list()
        self.get_module_list()

    def get_module_by_last_search_id(self, id):
        """ Return a tuple containing a ModuleModel and an AbilityBase

        """
        if 1 <= id <= len(self._last_search_results):
            return (  # id starts at 1
                module_factory.ModuleFactory.get_module(self._last_search_results[id-1][0], self._view),
                self._last_search_results[id-1][1]
            )
        return None

    def get_available_tags(self):
        """ Return a list of all declared Tags """
        if len(self._ability_tags) == 0:
            for pkg_path, list_abl in self._module_list.iteritems():
                for abl in list_abl:
                    self._ability_tags.update(
                        {tag.lower() for tag in abl.get_tags()}
                    )
        return self._ability_tags

    def get_module_name_words(self):
        """ Return a list of all used words (lower case) in module names for completion """
        if len(self._ability_name_words) == 0:
            for pkg_path, list_abl in self._module_list.iteritems():
                for abl in list_abl:
                    self._ability_name_words.update(
                        {word.lower() for word in abl.get_name().split(' ')}
                    )
        return self._ability_name_words

    def get_module_list(self):
        """ return the complete list of module, and keep it in memory
        the memory is used to propose a list of results like:
        > list
        1 ability/truc.py
        2 ability/truc1.py

        so a user can use it with:
        >use 1

        For now, only self.module_list is used (as the search function is not yet implemented)
        we can use directly the full list of modules
        """
        last_search = []
        returned_list = []
        for pkg_path, abl_group in self._module_list.items():
            last_search += [
                (pkg_path, abl)
                for abl in abl_group
            ]
            returned_list += abl_group
        self._last_search_results = last_search
        return returned_list

    def search_module(self, pattern, tags, search_all_tags):
        """search module path returns only module paths that contain a certain expression s

        all searches are lowercase

        :param pattern str: the expression to search for
        :param tags: set of Str, tags returned ability must have
        :param search_all_tags: 
            True -> all tags must be present to match (and relationship), 
            False -> at least 1 (or relationship)
        :return: the list of matching modules
        """
        pattern = pattern.lower()
        tags = [tag.lower() for tag in tags]

        last_search = []
        returned_list = []

        for pkg_path, abl_group in self._module_list.items():
            for abl in abl_group:
                if pattern not in abl.get_name().lower():
                    continue

                abl_tags = [tag.lower() for tag in abl.get_tags()]
                verdict = True
                for tag in tags:
                    if tag in abl_tags:
                        if not search_all_tags:
                            break
                    elif search_all_tags:
                        verdict = False
                        break

                if verdict:
                    returned_list.append(abl)
                    last_search.append((pkg_path, abl))

        self._last_search_results = last_search
        return returned_list

    def _refresh_module_list(self, limit=None):
        """ Build the list of available modules
        :param limit: (future) limit the refresh to a specific path
        :return: list of modules, (key is the relative path)
        """
        searched_path = [limit] if limit is not None else self._paths
        for pkg_path in searched_path:
            m = module_factory.ModuleFactory.get_module(pkg_path, self._view)
            self._module_list[pkg_path] = m.get_standalone_abilities()
