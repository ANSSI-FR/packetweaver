# coding: utf8
import abc
import cmd
import inspect
import os
import pipes
import sys
import readline
import traceback
import packetweaver.libs.sys.path_handling as path_ha
import packetweaver.core.views.text as output
import packetweaver.core.views.view_interface as view_interface
import packetweaver.core.models.abilities.ability_base as ability_base
import packetweaver.core.models.modules.ability_module as abl_module
import packetweaver.core.models.modules.module_factory as module_factory
import packetweaver.core.models.modules.module_option as module_option
import packetweaver.core.controllers.ctrl as ctrl
import packetweaver.core.controllers.kbd_exception as kbd_exception
import packetweaver.core.models.app_model as app_model
# for future python 3 compatibility
if sys.version_info > (3, 0):
    import configparser as config_parser
else:
    import ConfigParser as config_parser


class ShellUseCtrl(cmd.Cmd, ctrl.Ctrl):
    def __init__(self, module, ability, app_model, module_factory, view=output.Log()):
        """ Subshell to control an ability

        This is the "level 2" shell, used to setup and run an ability selected with the ShellCtrl shell.

        :param module: the model used to handle the ability
        :param ability: the ability to instantiate (AbilityBase)
        :param app_model: an AppModel that represents the software configuration
        :param view: a ViewsInterface subclass to handle the interface display
        """
        super(ShellUseCtrl, self).__init__()
        self._module = module
        self._ability = ability
        self._app_model = app_model
        self._module_factory = module_factory
        self._set_new_module_inst()
        self._view = view

    def _set_new_module_inst(self, cur_mod_inst=None):
        new_mod_inst = self._module.get_ability_instance_by_name(self._ability.get_name(), self._module_factory)
        self._ability = type(new_mod_inst)

        if cur_mod_inst is not None:
            new_opt_list = new_mod_inst.get_option_list()
            for opt_name in cur_mod_inst.get_option_list():
                if opt_name not in new_opt_list:
                    continue
                try:
                    new_mod_inst.set_opt(opt_name, cur_mod_inst.get_opt(opt_name, interpreted=False))
                except AssertionError:
                    self._view.warning('Old value for {} is incompatible with new definition'.format(opt_name))

        self._module_inst = new_mod_inst

    def get_pkg_abs_path(self):
        """ Return the absolute path of the current PacketWeaver package

        The package base folder is defined as the parent directory of the 'abilities' folder.

        :return: the absolute path of the package
        """
        abs_abl_path = path_ha.get_abs_path(self._module.get_module_path())
        return os.path.dirname(abs_abl_path)

    def define_rel_path(self, path_):
        pass

    def emptyline(self):
        """ Cmd() library specific need

        It needs to be overridden so that validating an empty line does not
        repeat the last cmd.
        """
        pass

    def do_shell(self, s):
        """
        Execute a command in a standard shell

        The "!" character can be used instead of the "shell" keyword

        Example:
            > shell python
            > !ip a

        The current directory is set on the current ability package path.
        """
        os.system(s)

    def do_editor(self, s=''):
        """
        Open the current ability and its dependencies in an external editor.

        The default editor used is the one specified in the software configuration file.
        """
        # Stores a list of abilities that are already added to the list of file to edit;
        # This variable is used to prevent infinite dependency import loops
        imported_abilities = []
        abilities = [self._ability]  # Stack of Abilities whose source file will be edited
        files = set()  # List of files to be edited

        while len(abilities) > 0:
            ability = abilities.pop(0)

            # Get this ability dependencies so that we fetch all dependencies recursively
            new_abls = []
            for dep in ability.get_dependencies().values():
                pkg = self._module_factory.get_module_by_name(dep.package)
                abl = type(pkg.get_ability_instance_by_name(dep.ability, self._module_factory))
                if abl not in abilities and abl not in imported_abilities:
                    new_abls.append(abl)
            imported_abilities += new_abls
            abilities += new_abls

            # Get the source file of the current ability
            fn = inspect.getsourcefile(ability)
            files.add(fn)

        editor = self._app_model.get_editor()
        if editor is None:
            self._view.warning('No editor configured.')
            return

        self.do_shell('{} {}'.format(editor, ' '.join(files)))
        self.reload()

    def do_run(self, s=''):
        """
        Execute an ability using the current option values.

        Its content is automatically reloaded.
        """
        self.run(s)

    def run(self, s=''):
        """ Method called by the do_run method """
        try:
            # Renew the current module because if we are re-running, we cannot start a thread twice!
            self._set_new_module_inst(self._module_inst)
            self._module_inst.start()
            while not self._module_inst.is_stopped():
                try:
                    self._module_inst.join(0.1)
                except kbd_exception.CtrlC:
                    self._module_inst.stop()
            self._module_inst.join(0.1)
            ret = self._module_inst.result()
            if ret is not None:
                self._view.success(str(ret))
        except:
            self._view.error("Error running the module")
            traceback.print_exc()
            self._module_inst.stop()
            self._module_inst.join(0.1)
        finally:
            self._set_new_module_inst(self._module_inst)

    def do_cmd(self, s=''):
        """
        Generate a command line to call the
        ability with the current parameters from
        a standard system's script.

        Your can specify the 'oneline' argument to have
        a one-line version to run the ability directly
        from a system's shell.
        """
        self._view.delimiter("Cmd to replay the module")
        options, command = self._generate_command()
        if s == "oneline":
            sep = ' '
            self._view.info('{}{};{}'.format(sep.join(options), sep, command))
        else:
            sep = '\n'
            self._view.info('{}{}{}'.format(
                sep.join(['export {}'.format(opt) for opt in options]),
                sep, command
            ))

    def _generate_command(self):
        """ Generate a command to run the ability with its current configuration using the command line
        software's interface """
        opt_list = type(self._module_inst).get_option_list()
        # cast to string so number get correctly handled
        options = [
            "PW_OPT_{}='{}'".format(
                opt_name.upper(), pipes.quote(
                    str(self._module_inst.get_opt(opt_name, interpreted=False))
                )
            )
            for opt_name in opt_list
        ]

        options.append("PYTHONPATH='{}'".format(pipes.quote(':'.join(sys.path))))

        cmd_options = [
            '--{}=${{PW_OPT_{}}}'.format(opt_name, opt_name.upper())
            for opt_name in opt_list
        ]

        command = 'python {} use -p {} -a {} {}'.format(
            sys.argv[0],
            pipes.quote(self._app_model.get_package_name_by_path(self._module.get_module_path())),
            pipes.quote(type(self._module_inst).get_name()),
            ' '.join(cmd_options)
        )
        return options, command

    def complete_cmd(self, text, _line, begidx, endidx):
        """ Autocomplete the 'oneline' parameter tha generate a
        online command.
        """
        l_options = ('oneline',)
        return [i for i in l_options if i.startswith(text)]

    def do_set(self, s):
        """
        Modify an input parameter of the ability.
        Available options can be seen with the "options"
        command.

        Completion is available to use specific random value
        generators.

        Examples:
            > set ip_src=192.168.0.2
            > set mac_dst=RandMac

        See the "clear" command to get back the default
        value of a parameter (i.e as written in the source
        code)
        """
        # identify the parameter and the value
        try:
            pos = s.find('=')
            if pos == -1:
                raise ValueError
            opt_name, opt_val = s[:pos], s[pos + 1:]
            self._module_inst.set_opt(opt_name, opt_val)
        except ValueError:
            self._view.error("> Invalid option, please check your parameters")
        except AssertionError:
            self._view.error("> Invalid option, please check your parameters")

    def complete_set(self, text, line, begidx, endidx):
        """ Provide completion for the "set" option

        Autocomplete the option name and append a "="
        Autocomplete accessible random value generators
        available for the concerned parameter.
        """
        try:
            # complete with available options - suppose only one =, no spaces
            if "=" in line:
                option_name, arg_typed = line[line.find(' ')+1:].split("=")
                l = self._module_inst.get_possible_values(
                    option_name,
                    arg_typed,
                    self.get_pkg_abs_path()
                )
                last_completer_delim_index = -1
                for delim in readline.get_completer_delims():
                    last_completer_delim_index = max(last_completer_delim_index, arg_typed.rfind(delim))

                return [
                    val
                    for val in l
                    if self._module_inst.is_a_valid_value_for_this_option(
                        option_name, arg_typed[:last_completer_delim_index+1] + val
                    )
                ]
            else:
                return [
                    '{}='.format(i)
                    for i in type(self._module_inst).get_option_list()
                    if i.startswith(text)
                ]
        except:
            # display completion method crash message until not covered by tests
            traceback.print_exc()

    def do_options(self, s=''):
        """
        Display ability parameters

        - Options are in the same order as they are
        described in the source code.
        - Parameter values having their default value
        are displayed in bold
        - Parameter with local values are displayed in
        blue.
        """
        options = self._module_inst.get_option_list()
        self._view.delimiter("Options")

        if len(options) == 0:
            self._view.info("No options available")
            self._view.delimiter()
            return

        for opt_name in options:
            if len(s) == 0 or s.lower() == opt_name.lower():
                if self._module_inst.has_default_value(opt_name):
                    val = self._view.with_effect('bold', str(self._module_inst.get_opt(opt_name, interpreted=False)))
                else:
                    val = self._view.with_color('blue', self._module_inst.get_opt(opt_name, interpreted=False))

                comment = type(self._module_inst).get_option_comment(opt_name)
                optional = type(self._module_inst).get_optional_status(opt_name)
                if comment is not None and len(comment) > 0:
                    if optional:
                        additional_info = ' ({}, Optional)'.format(comment)
                    else:
                        additional_info = ' ({})'.format(comment)
                elif optional:
                    additional_info = ' (Optional)'
                else:
                    additional_info = ''
                self._view.info('{}{} = {}'.format(opt_name, additional_info, val))

        self._view.delimiter()

    def do_info(self, s=''):
        """
        Display ability's information
        """
        info = self._ability.get_metadata()

        self._view.delimiter(info.get_name())
        for k, v in [(k, v) for k, v in info.summary() if k != 'name' and (len(s) == 0 or s == k)]:
            self._view.info('{}: {}'.format(self._view.with_effect('bold', str(k)), v))
        self._view.delimiter()

    def do_reload(self, s=''):
        """
        Manually reload the module with the last
        saved version from the source code

        Current local values of the parameters
        will be kept. See the "clear" command to
        set them to their default values.
        """
        self.reload(s)

    def reload(self, s=''):
        """ Reload the ability """
        try:
            self._module = type(self._module_factory).get_module(self._module.get_module_path(), self._view)
            self._set_new_module_inst(self._module_inst)
        except SyntaxError:
            self._view.error("SyntaxError")
            traceback.print_exc()
            self._view.error("> The module has NOT be reloaded")

    def can_exit(self):
        """ Used to prevent exiting the shell """
        return True

    def do_clear(self, s=''):
        """
        Restore an ability's parameter to its
        default value as written in the last
        saved version of the source code.

        You can specify a parameter name to
        reset only its value.

        Example:
            > clear [parameter_name]
        """
        if len(s) > 0:
            self._module_inst.clear_option(s)
        else:
            self._module_inst.clear_options()

    def complete_clear(self, text, line, begidx, endidx):
        """ Autocomplete parameter names to selectively clear a parameter value """
        l_options = self._module_inst.get_option_list()
        return [i for i in l_options if i.startswith(line[begidx:])]

    def do_exit(self, s=''):
        """
        Exit the shell after saving the shell history
        You can also use the Ctrl-D shortcut
        """
        raise kbd_exception.CtrlD()

    do_EOF = do_exit

    def do_howto(self, _):
        """
        Prints an ability-specific manual page.
        
        Its content is let free to the developer, who can use it
        to explain the ability use case, configuration details 
        or any other information.
        """
        self._module_inst.howto()

    def do_save(self, filename):
        """
        Saves the current ability configuration into a file, 
        which can be loaded back with the "load" command
        
        Example:
            save /tmp/my_abl
        """
        filename = path_ha.get_abs_path(filename, self.get_pkg_abs_path())
        if not os.access(filename, os.F_OK):
            try:
                open(filename, 'w').close()
            except IOError:
                self._view.error('File "{}" cannot be created.'.format(filename))
                return

            cp = config_parser.ConfigParser()
            options = {}
        else:
            if not os.access(filename, os.W_OK):
                self._view.error('File "{}" is not writable.'.format(filename))
                return
            cp = config_parser.ConfigParser()
            try:
                cp.readfp(open(filename, 'r'))
            except:
                self._view.error('Invalid/Ill-formated configuration file: {}'.format(filename))
                return

            try:
                options = dict(cp.items('Configuration'))
            except config_parser.NoSectionError:
                options = {}

        for opt_name in type(self._module_inst).get_option_list():
            options[opt_name] = self._module_inst.get_opt(opt_name, interpreted=False)

        try:
            cp.add_section('Configuration')
        except config_parser.DuplicateSectionError:
            pass

        for key, val in options.items():
            cp.set('Configuration', key, val)

        cp.write(open(filename, 'w'))
        self._view.info('Current option values have been saved to {}.'.format(filename))

    def do_load(self, filename):
        """
        Loads options for the current ability from a specified 
        configuration file.
        
        Any incorrect values in the option file is simply ignored.
        Relative file name will start from the current ability package path.
        
        Example:
            load /tmp/my_abl
        """
        filename = path_ha.get_abs_path(filename, self.get_pkg_abs_path())
        if not os.access(filename, os.R_OK):
            self._view.error('Unreadable file: {}'.format(filename))
            return
        cp = config_parser.ConfigParser()

        try:
            cp.readfp(open(filename, 'r'))
        except:
            self._view.error('Invalid/Ill-formated configuration file: {}'.format(filename))
            return

        try:
            options = dict(cp.items('Configuration'))
        except config_parser.NoSectionError:
            self._view.error('Invalid/Ill-formated configuration file: {}'.format(filename))
            return

        for opt_name, opt_value in options.items():
            try:
                self._module_inst.set_opt(opt_name, opt_value)
            except AssertionError:
                pass

    def complete_load(self, text, line, begidx, endidx):
        """ Provide completion for the "load" option

        Autocomplete the path of the file to load
        """
        try:
            path = line[line.find(' ')+1:]
            return [
                candidate
                for candidate in module_option.PathOpt.get_possible_values(
                    path,
                    self.get_pkg_abs_path()
                )
                if candidate.startswith(text)
            ]
        except:
            # display completion method crash message until not covered by tests
            traceback.print_exc()

    complete_save = complete_load
