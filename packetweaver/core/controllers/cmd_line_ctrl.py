# coding: utf8
import signal
import argparse
import packetweaver.core.models.module_list_model as modulelistmodel
import packetweaver.core.models.modules.module_factory as module_factory
import packetweaver.core.views.text as output
import packetweaver.core.views.view_interface as view_interface
import packetweaver.core.controllers.ctrl as ctrl
import packetweaver.core.controllers.kbd_exception as kbd_exception
import packetweaver.core.models.app_model as app_model

def handle_ctrlc(_signum, _frame):
    """
    @raise kbd_exception.CtrlC
    """
    print("")
    raise kbd_exception.CtrlC()


signal.signal(signal.SIGINT, handle_ctrlc)


class CmdLineCtrl(ctrl.Ctrl):
    def __init__(self, cli_args, rem_args, app_model, module_factory, view=output.Log()):
        """ Handle the command line interface of the software

        :param cli_args: argparse successfully parsed arguments
        :param rem_args: list of argument not parsed by argparse
        :param app_model: an AppModel that represent the software configuration
        :param module_factory: the module factory to pass to the instantiated abilities
        :param view: a ViewsInterface subclass to handle user interface display
        """
        super(CmdLineCtrl, self).__init__()
        self._cli_args = cli_args
        self._rem_args = rem_args
        self._parsed_args = None
        self._argparser = None
        self._app_model = app_model
        self._module_factory = module_factory
        self._module_list_model = modulelistmodel.ModuleListModel(self._app_model.get_packages())
        self._view = view

    def _pre_process_run(self):

        module_path = self._app_model.get_config('Packages', self._cli_args.package_name)
        if module_path is None:
            msg = 'Unknown package: {}'.format(self._cli_args.package_name)
            self._view.error(msg)
            raise Exception(msg)

        self._module = type(self._module_factory).get_module(module_path, view=self._view)
        self._module_inst = self._module.get_ability_instance_by_name(self._cli_args.ability_name, self._module_factory)
        if self._module_inst is None:
            msg = 'Unknown ability: {}'.format(self._cli_args.ability_name)
            self._view.error(msg)
            raise Exception(msg)

        # Get all options
        opts = self._module_inst.get_option_list()

        # Generate a parser ready to fetch any option by that name
        self._argparser = argparse.ArgumentParser()
        for x in opts:
            self._argparser.add_argument('--{}'.format(x), type=str, dest=x, required=False)
        self._argparser.add_argument('--modhelp', action='store_true', dest='help',
                                     help='Print context-specific module help message')

        # Parse the actual command line string
        self._parsed_args = self._argparser.parse_args(self._rem_args)

        # set the default module options for any option that was discovered by the cli parser
        options = {
            x: getattr(self._parsed_args, x)
            for x in opts
            if hasattr(self._parsed_args, x) and getattr(self._parsed_args, x) is not None
        }
        for k, v in options.items():
            self._module_inst.set_opt(k, v)

    def pre_process(self):
        """ Parse the first  """
        # parse command line by hand, get parameters and display errors
        cmd = self._cli_args.subcmd
        if cmd in ['run', 'start', 'exploit', 'use']:
            self._pre_process_run()

    def process(self):
        cmd = self._cli_args.subcmd
        if cmd in ['show', 'list']:
            self._list_modules()
            return
        if getattr(self._parsed_args, 'help'):
            self._argparser.print_help()
            return

        res = self._module_inst.start()

    def _list_modules(self):
        """ Display the list of available abilities """
        for abl in self._module_list_model.get_module_list():
            self._view.info(abl.get_name())
