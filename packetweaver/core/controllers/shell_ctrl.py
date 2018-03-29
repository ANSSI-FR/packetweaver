# coding: utf8
import os
import re
import cmd
import signal
import readline
import traceback
import packetweaver.core.controllers.exceptions as ex
import packetweaver.libs.gen.pwcolor as pwc
import packetweaver.core.models.module_list_model as module_list_model
import packetweaver.core.models.modules.module_factory as module_factory
import packetweaver.core.views.view_interface as view_interface
import packetweaver.core.views.text as output
import packetweaver.core.controllers.kbd_exception as kbd_exception
import packetweaver.core.controllers.ctrl as ctrl
import packetweaver.core.controllers.shell_use_ctrl as shell_use_ctrl
import packetweaver.core.models.abilities.ability_base as ability_base
import packetweaver.core.models.app_model as app_model


class ShellCtrl(cmd.Cmd, ctrl.Ctrl):
    def __init__(self, app_model, module_factory, view=output.Log()):
        """ Handle the interactive shell

        This is the "level 1" shell, used to browse and select available abilities. It use the Cmd python library to
        provide commands, help messages and completion.

        A second shell is called by the do_use() method : ShellUseCtrl.

        :param app_model: an AppModel that represent the software configuration
        :param view: a ViewInterface subclass to handle user interface display
        """
        super(ShellCtrl, self).__init__()

        self._view = view
        # documentation view customization
        self.ruler = "="
        self.doc_header = "Documented commands (type help <topic>):"
        self.misc_header = "Miscellaneous help topics:"
        self.undoc_header = "Undocumented commands:"
        self._app_model = app_model
        self._module_factory = module_factory
        self._search_and_opt_name = '-a'
        self._search_or_opt_name = '-o'

        self.prompt = self._app_model.app_prompt_l1
        try:
            self._history_path = self._app_model.get_hist_file_path()
        except ex.ConfHistFileNotAccessible as e:
            self._view.error('{}'.format(e))
            raise ex.ExitPw()
        readline.read_history_file(self._history_path)

        try:
            l_pkg = self._app_model.get_packages()
        except ex.ConfNone:
            l_pkg = []
        self._module_list_model = module_list_model.ModuleListModel(l_pkg)
        _ = self._module_list_model.get_module_list()  # load the search result indexes with default values

        signal.signal(signal.SIGINT, self._handle_ctrlc)

        self.doc_leader = \
            """
    {} ({}) - v.{}
    {}
    
    Use the 'help' or '?' command to discover available commands. 
    Use 'tab' to complete any part of your input.
    
    """.format(self._app_model.app_name,
               self._app_model.app_name_abbrev,
               self._app_model.app_version,
               self._app_model.app_slogan)

    def _handle_ctrlc(self, _signum, _frame):
        """ Handle sigint signal and use it to start a new shell line (through CtrlC exception) """
        self._view.info("")
        raise kbd_exception.CtrlC()

    def _display_banner(self):
        # Display software banner, slogan and version
        self._view.delimiter()
        c = lambda color_name, s: self._view.with_color(color_name, s.strip())
        self._view.info("o-o  {}   o   o\n".format(c('blue', 'o')) +
                        "|  |  \ / \ /   {}\n".format(
                            self._app_model.app_name) +
                        "{}-o    o   {}    {}\n".format(c('yellow', 'O'),
                                                        c('green', 'o'),
                                                        self._app_model.app_slogan) +
                        "|               v.{}\n".format(
                            self._app_model.app_version) +
                        "o".format(self._app_model.app_name,
                                   self._app_model.app_version))
        self._view.delimiter()

    def process(self):
        """ Run the interactive shell after displaying the software version information

        @raise SystemExit
        """
        self._display_banner()

        while 1:
            try:
                self.cmdloop()
            except kbd_exception.CtrlD:
                signal.signal(signal.SIGINT, signal.SIG_DFL)
                return
            except kbd_exception.CtrlC:
                # cancel the current line and get a new one
                pass

    def emptyline(self):
        """ Cmd() library specific need

        It needs to be overridden so that validating an empty line does not
        repeat the last cmd
        """
        pass

    def do_shell(self, s=''):
        """
        Execute a command in a standard shell

        The "!" character can be used instead of the "shell" keyword

        Example:
            > shell python
            > !ip a

        The current directory is on your PacketWeaver pw.py file.
        """
        os.system(s)

    def _list(self, s=''):
        """ List all available abilities """
        l_abl = self._module_list_model.get_module_list()
        if len(l_abl) == 0:
            self._view.error('No ability yet :(')
            return

        for i, val in enumerate(l_abl):
            color = '' if len(val.check_preconditions(self._module_factory)) == 0 else 'red'
            self._view.info(
                self._view.with_color(
                    color, '{} {} -- {}'.format(i+1, val.get_name(), ', '.join(val.get_tags()))
                )
            )

    do_list = _list
    do_ls = _list

    def _split_search_pattern_and_tags(self, s):

        opts = [elmt for elmt in s.split(' ') if elmt != '']
        try:
            and_opt_index = opts.index(self._search_and_opt_name)
        except ValueError:
            and_opt_index = -1
        try:
            or_opt_index = opts.index(self._search_or_opt_name)
        except ValueError:
            or_opt_index = -1

        if and_opt_index != -1:
            if or_opt_index != -1:
                self._view.warning(
                    'Cannot use both {} and {} arguments in a search.'.format(
                        self._search_and_opt_name, self._search_or_opt_name
                    )
                )
                return '', set(), True
            return ' '.join(opts[:and_opt_index]), set(opts[and_opt_index + 1:]), True
        elif or_opt_index != -1:
            return ' '.join(opts[:or_opt_index]), set(opts[or_opt_index+1:]), False
        return ' '.join(opts), set(), True

    def do_search(self, s=''):
        """
        Search in abilities by name and/or by tag

        Example:
            > search string
            > search [string] -a tag1 tag2
            > search [string] -o tag1 tag2

        -a : abilities must have all specified tags
        -o : abilities must have one of the specified tags

        Options -a et -o cannot be used simultaneously.
        If no arguments are provided, "search" is equivalent
        to the "list" command.

        Note: completion on tags and string is enabled, everything
        is processed lower case.
        """
        if len(s) == 0:
            self._list()
            return

        pattern, tags, all_tags = self._split_search_pattern_and_tags(s)
        # search modules and display results
        matching_abilities = self._module_list_model.search_module(pattern, tags, all_tags)

        if len(matching_abilities) == 0:
            self._view.warning('No matching ability found.')
            return

        # highlight results and display them
        for i, match_abl in enumerate(matching_abilities):
            # display in red if the ability is missing a dependency
            color = '' if len(match_abl.check_preconditions(self._module_factory)) == 0 else 'red'

            # highlight the search pattern ability names
            name_highlighted = re.sub(
                pattern, self._view.with_effect('bold', pattern, color), match_abl.get_name(), flags=re.I
            )

            # underline matching tags
            tags_highlighted = ', '.join(match_abl.get_tags())
            for searched_tag in tags:
                tags_highlighted = re.sub(
                    searched_tag, self._view.with_effect('underline', searched_tag, color),
                    tags_highlighted, flags=re.I
                )
            self._view.info(self._view.with_color(color, '{} {} -- {}'.format(i+1, name_highlighted, tags_highlighted)))

    def complete_search(self, text, line, begidx, endidx):
        """ Add completion to existing word and available tags after a '-a'
        or '-o' option """
        before_arg = line.rfind(" ", 0, begidx)
        if before_arg == -1:
            return None
        # list available tags after a "-t " or "-a "
        if self._search_and_opt_name in line or self._search_or_opt_name in line:
            # return a space right after a "-t" or "-a" when hitting <Tab>
            if line.endswith(self._search_and_opt_name):
                return ['{} '.format(self._search_and_opt_name[1:])]
            elif line.endswith(self._search_or_opt_name):
                return ['{} '.format(self._search_or_opt_name[1:])]
            return [
                '{} '.format(t[begidx - before_arg - 1:])
                # add space to suggest the cmd can be continued
                for t in self._module_list_model.get_available_tags()
                if t.startswith(line[before_arg + 1:endidx])
            ]
        elif line[before_arg + 1:endidx] == '-':
            return [self._search_and_opt_name[1:], self._search_or_opt_name[1:]]
        
        # list existing keyword
        return [
            t[begidx - before_arg - 1:]
            for t in self._module_list_model.get_module_name_words()
            if t.startswith(line[before_arg + 1:endidx])
        ]

    def _normalize_search_index(self, s):
        """ Validate and normalize the entered search index

        :param s: string passed to a command asking for a search index
        :return: integer
        """
        if len(s) == 0:
            return 1
        else:
            try:
                return int(s)
            except ValueError:
                raise

    def _get_module_from_search_index(self, index):
        """

        :param index: the parameters passed to a command awaiting for an index
        :return:
        """
        try:
            index_normalized = self._normalize_search_index(index)
            return self._module_list_model.get_module_by_last_search_id(index_normalized)
        except ValueError:
            self._view.error('You must specify the ability index given by you last list/search command')
            return

    def do_conf(self, s=''):
        """
        Open the PacketWeaver configuration file
        in your editor.

        /!\ You will have to restart the framework
        in order to apply your modifications. /!\
        """
        conf_file_path = self._app_model.get_config_file_path()
        try:
            editor = self._app_model.get_editor()
        except ex.ConfEditorNone as e:
            self._view.warning('{}'.format(e))
            return
        self.do_shell('{} {}'.format(editor, conf_file_path))
        self._view.warning('Please restart the framework in order to apply your modifications.')

    def do_editor(self, s=''):
        """
        Open the ability and its dependencies source files
        in an editor using the last search index as
        displayed by the last list/search command
        """
        ret = self._get_module_from_search_index(s)
        if ret is None:
            self._view.error('Unable to find the module. Did you perform a list/search command beforehand?')
            return
        module, selected_ability = ret
        files = selected_ability.get_dep_file_paths(self._module_factory)
        try:
            editor = self._app_model.get_editor()
        except ex.ConfEditorNone as e:
            self._view.warning('{}'.format(e))
            return
        self.do_shell('{} {}'.format(editor, ' '.join(files)))

    def do_use(self, s=''):
        """
        Select the ability to load using its index
        as displayed by the last list/search command

        Examples:
            > use     # a shortcut to > use 1
            > use 4
        """
        ret = self._get_module_from_search_index(s)
        if isinstance(ret, type(None)):
            self._view.error('Unable to find the module. Did you perform a list/search command beforehand?')
            return
        module, ability = ret

        if module is None:
            self._view.warning('No module found by that "id".')
            return
        try:
            l = ability.check_preconditions(self._module_factory)
            if len(l) > 0:
                self._view.error('\n'.join(l))
                raise Exception('Ability cannot be started; some prerequisites are missing.')

            u = shell_use_ctrl.ShellUseCtrl(
                module,
                ability,
                self._app_model,
                self._module_factory,
                view=self._view
            )
        except SyntaxError:
            self._view.error("The module has NOT be loaded, please check your module's code")
            return
        except ImportError:
            self._view.error("The module cannot be found, make sure it exists and is in a python package (__init__.py)")
            return
        except:
            traceback.print_exc()
            self._view.error("> Module could not be loaded, please check the previous error message")
            return

        # compact path in the module prompt if absolute path
        u.prompt = self._app_model.app_prompt_l2.format(
            self._view.with_color("green", ability.get_name()))

        while 1:
            try:
                prev_dir = os.getcwd()
                os.chdir(u.get_pkg_abs_path())
                u.cmdloop()
            except kbd_exception.CtrlD:
                self._view.info("")
                break
            except kbd_exception.CtrlC:
                pass
            finally:
                os.chdir(prev_dir)

    def can_exit(self):
        """ Used to prevent exiting the shell """
        return True

    def do_exit(self, s=''):
        """
        Exit the shell after saving the shell history
        You can also use the Ctrl-D shortcut
        """
        readline.write_history_file(self._history_path)
        raise kbd_exception.CtrlD()

    do_EOF = do_exit
