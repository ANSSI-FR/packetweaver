import abc
import logging
import collections
import copy
import inspect
import packetweaver.core.models.abilities.ability_dependency
import packetweaver.core.models.abilities.ability_info as ability_info
import packetweaver.core.models.modules.module_factory
import packetweaver.core.models.modules.module_option as module_option
import packetweaver.core.models.status as status
import packetweaver.core.views.text as output


OptionTemplateEntry = collections.namedtuple(
    'OptionTemplateEntry', ['validator', 'entry']
)

"""
OptionTemplateEntry is the definition of one of the options of this ability.
The validator is a callable that returns a boolean. True means that the
provided value follows a suitable format for this entry.

Validator receives two parameters:
- the ModuleOption instance received provided in the template
- the value to validate
"""


class AbilityBase(object):
    """ The base abstract class to implement new abilities
    """
    __metaclass__ = abc.ABCMeta

    _option_list = []
    _opt_hash = None
    _info = ability_info.AbilityInfo(
        name='AbilityBase',
        description='Base class; does nothing',
        authors=['John Doe'],
        references=[[]],
        diffusion='internal',
        tags=[],
        reliability=status.Reliability.INCOMPLETE,
        type=status.AbilityType.STANDALONE
    )
    _dependencies = []
    _internal_dependencies = None
    """:var _option_list: defines the list of options for this ability and
    the default values ; an entry in this dict can either be a plain
    ModuleOption or a OptionTemplateEntry. The difference is in the validation.
     If it is a ModuleOption, a call to the is_valid method is performed on
     this ModuleOption instance, with as single argument the value to validate.
    If it is a OptionTemplateEntry, then the "validator"
    member is called, with two arguments: the entry ModuleOption instance and
    the value to validate.
    :var _info: XXX
    """

    @classmethod
    def _init_opt_hash(cls):
        if cls._opt_hash is not None:
            return
        cls._opt_hash = {}
        for opt in cls._option_list:
            if isinstance(opt, OptionTemplateEntry):
                opt = opt.entry
            cls._opt_hash[opt.get_name()] = opt

    @classmethod
    def _init_internal_dependencies(cls):
        if cls._internal_dependencies is not None:
            return
        cls._internal_dependencies = {}
        for entry in cls._dependencies:
            if isinstance(entry, str):
                cls._internal_dependencies[entry] = \
                    packetweaver.core.models.abilities.ability_dependency\
                    .get_classic(entry)
            elif isinstance(entry, tuple):
                cls._internal_dependencies[entry[0]] = \
                    packetweaver.core.models.abilities.ability_dependency\
                    .AbilityDependency(entry[1], entry[2])
            else:
                raise Exception(
                    'Unknown dependency type: {}'.format(type(entry))
                )

    @classmethod
    def check_preconditions(cls, module_factory):
        cls._init_internal_dependencies()
        l_dep = []
        for dep in cls._internal_dependencies.keys():
            inst = cls.cls_get_dependency(dep, module_factory)
            if inst is None:
                raise Exception('Unknown dependency: {}'.format(dep))
            l_dep += type(inst).check_preconditions(module_factory)
        return set(l_dep)

    def __init__(self, module_factory, default_opts=None, view=output.Log()):
        """ Create a new ability

        An ability is a class stored at a meaningful place in the module tree
        (the default or your) This class must be sub-classed to implement
        a new simple ability.

        :param module_factory: the factory used to instantiate dependencies
        :param default_opts: ability parameters values to be used as default
        :param view: a ViewsInterface subclass to handle the interface display
        """
        type(self)._init_opt_hash()
        type(self)._init_internal_dependencies()
        super(AbilityBase, self).__init__()
        self._module_factory = module_factory
        self._view = view
        self._cached_opt_values = {}
        self._ret_value = None
        self._alive = True
        self._started_status = False
        self._set_default_opts(default_opts)
        self.logger = logging.getLogger(__name__)

    def _set_default_opts(self, default_opts=None):
        self._set_options(type(self)._opt_hash)

        if default_opts is not None:
            self._default_opts = copy.deepcopy(default_opts)
        if self._default_opts is not None:
            for opt_name, opt_value in self._default_opts.items():
                self.set_opt(opt_name, opt_value)

    clear_options = _set_default_opts

    def clear_option(self, name):
        """ Restore default values to the options

        Reset all options to their default value. If a name is provided,
        only this specific option will be reset.

        :param name: name of the option to reset
        """
        if name in self._default_opts:
            v = self._default_opts[name].get_value()
        else:
            v = type(self)._opt_hash[name].get_value()
        self.set_opt(name, v)

    def _set_options(self, opts):
        """ Affect a whole option values

        The opts will erase the current options dictionary.
        :param opts: a dictionary containing names and ModuleOption objects
        """
        self._options = {k: opt.get_value() for k, opt in opts.items()}

    def set_opts(self, **kwargs):
        """ Setup several arguments at the same time

        :param kwargs: list of option_name='val' to affect to the abilitiy
        @Raise Exception
        """
        for opt in kwargs:
            try:
                self.set_opt(opt, kwargs[opt])
            except Exception:
                raise Exception('Invalid parameter')

    def set_opt(self, opt_name, opt_value):
        """ Set a value to a specific option and check

        The validity to the option format is checked. A exception is raised
        if the check fails.

        :param opt_name: name of the option
        :param opt_value: value to affect to this option
        @raise AssertionError
        """
        if self._is_started():
            raise Exception('Cannot define options once started!')

        assert (
            opt_name in type(self)._opt_hash
            and (
                (
                    isinstance(type(self)._opt_hash[opt_name],
                               module_option.ModuleOption)
                    and (
                        type(self)._opt_hash[opt_name].is_valid(opt_value)
                        or (opt_value.endswith('()')
                            and type(self)._opt_hash[opt_name].is_valid(
                                opt_value[:-2])
                            )
                    )
                )
                or (
                    isinstance(type(self)._opt_hash[opt_name],
                               OptionTemplateEntry)
                    and type(self)._opt_hash.validator(
                        type(self)._opt_hash[opt_name],
                        opt_value
                    )
                )
            )
        ), 'Invalid option name or value for option {}: {}'.format(opt_name,
                                                                   opt_value)

        # Generate a value from the function
        if isinstance(opt_value, str) and opt_value.endswith('()'):
            if isinstance(type(self)._opt_hash[opt_name],
                          module_option.ModuleOption):
                opt_value = type(self)._opt_hash[opt_name].generate_one_value(
                    opt_value[:-2]
                )
            else:
                opt_value = type(self)._opt_hash[opt_name].entry.\
                    generate_one_value(opt_value[:-2])
        self._options[opt_name] = opt_value

        try:
            del self._cached_opt_values[opt_name]
        except KeyError:
            pass

    @classmethod
    def get_option_list(cls):
        cls._init_opt_hash()
        names = []
        for o in cls._opt_hash.values():
            if isinstance(o, module_option.ModuleOption):
                names.append(o.get_name())
            else:
                assert (isinstance(o, OptionTemplateEntry))
                names.append(o.entry.get_name())
        return names

    @classmethod
    def get_option_comment(cls, opt_name):
        cls._init_opt_hash()
        if opt_name not in cls._opt_hash:
            return ''
        if isinstance(cls._opt_hash[opt_name], module_option.ModuleOption):
            opt = cls._opt_hash[opt_name]
        else:
            opt = cls._opt_hash[opt_name].entry
        return opt.get_comment()

    @classmethod
    def get_optional_status(cls, opt_name):
        cls._init_opt_hash()
        if opt_name not in cls._opt_hash:
            return None
        if isinstance(cls._opt_hash[opt_name], module_option.ModuleOption):
            opt = cls._opt_hash[opt_name]
        else:
            opt = cls._opt_hash[opt_name].entry
        return opt.is_optional()

    @classmethod
    def get_name(cls):
        return cls._info.get_name()

    @classmethod
    def get_description(cls):
        return cls._info.get_description()

    @classmethod
    def get_tags(cls):
        return cls._info.get_tags()

    @classmethod
    def get_type(cls):
        return cls._info.get_type()

    @classmethod
    def get_dependencies(cls):
        return copy.deepcopy(cls._internal_dependencies)

    @classmethod
    def get_dep_file_paths(self, module_factory):
        """ Return the path of all the abilities the current ability depends on

        :return: list of paths to the required abilities
        """
        # Stores a list of abilities that are already added to the list of file
        # to edit;
        # This variable is used to prevent infinite dependency import loops
        imported_abilities = []
        abilities = [self]  # Stack of Abilities whose source file will be
        # edited
        files = set()  # List of files to be edited

        while len(abilities) > 0:
            ability = abilities.pop(0)

            # Get this ability dependencies so that we fetch all dependencies
            # recursively
            new_abls = []
            for dep in ability.get_dependencies().values():
                pkg = module_factory.get_module_by_name(dep.package)
                abl = type(pkg.get_ability_instance_by_name(dep.ability,
                                                            module_factory))
                if abl not in abilities and abl not in imported_abilities:
                    new_abls.append(abl)
            imported_abilities += new_abls
            abilities += new_abls

            # Get the source file of the current ability
            fn = inspect.getsourcefile(ability)
            files.add(fn)
        return files

    @classmethod
    def cls_get_dependency(cls, name, module_factory, params={}, **kwargs):
        if name not in cls._internal_dependencies:
            raise Exception('Unknown dependency: {}'.format(name))

        module = module_factory.get_module_by_name(
            cls._internal_dependencies[name].package
        )
        if module is None:
            raise Exception('Unknown package: {}'.format(
                cls._internal_dependencies[name].package)
            )

        ability = module.get_ability_instance_by_name(
            cls._internal_dependencies[name].ability,
            module_factory
        )

        for arg_name, arg_value in list(params.items()) + list(kwargs.items()):
            ability.set_opt(arg_name, arg_value)

        return ability

    def get_dependency(self, name, params={}, **kwargs):
        return type(self).cls_get_dependency(
            name, self._module_factory, params, **kwargs
        )

    def get_opt(self, name, interpreted=True, bypass_cache=False):
        """
        @raise AssertionError
        """
        assert (name in self._options)

        if not interpreted:
            try:
                return copy.deepcopy(self._options[name])
            except TypeError:
                return self._options[name]

        if bypass_cache or name not in self._cached_opt_values:
            if (
                name in self._cached_opt_values
                and isinstance(self._cached_opt_values[name], tuple)
                and len(self._cached_opt_values[name]) == 2
                and hasattr(self._cached_opt_values[name][1], 'next')
                and callable(self._cached_opt_values[name][1].next)
            ):
                val = self._cached_opt_values[name][1]
            elif isinstance(type(self)._opt_hash[name],
                            module_option.ModuleOption):
                val = type(self)._opt_hash[name].generate_one_value(
                    self._options[name])
            else:
                val = type(self)._opt_hash[name].entry.generate_one_value(
                    self._options[name])

            if hasattr(val, 'next') and callable(val.next):
                self._cached_opt_values[name] = next(val), val
            else:
                self._cached_opt_values[name] = val

        if isinstance(self._cached_opt_values[name], tuple):
            return self._cached_opt_values[name][0]
        return self._cached_opt_values[name]

    @classmethod
    def get_metadata(cls):
        return copy.deepcopy(cls._info)

    def get_possible_values(self, opt_name, typed, ref=None):
        """ Get suggestion on possible values for an option

        :param opt_name: name of the option
        :param typed: begin of the text submit to the module_option in order
            to get completion suggestions
        :param ref: custom data passed directly to the module_option by the
            ability
        @raise AssertionError
        """
        if opt_name not in type(self)._opt_hash:
            return []

        opt = type(self)._opt_hash[opt_name]
        if isinstance(opt, module_option.ModuleOption):
            return opt.get_possible_values(typed, ref)

        assert (isinstance(opt, OptionTemplateEntry))
        return opt.entry.get_possible_values(typed, ref)

    def is_a_valid_value_for_this_option(self, opt_name, value):
        if opt_name not in type(self)._opt_hash:
            return False
        opt = type(self)._opt_hash[opt_name]
        if isinstance(opt, module_option.ModuleOption):
            return opt.is_valid(value)

        assert (isinstance(opt, OptionTemplateEntry))
        return opt.validator(value)

    def has_default_value(self, opt_name):
        if opt_name not in self.get_option_list():
            return None

        if self._default_opts is not None and opt_name in self._default_opts:
            def_opt = self._default_opts[opt_name]
        elif isinstance(type(self)._opt_hash[opt_name],
                        module_option.ModuleOption):
            def_opt = type(self)._opt_hash[opt_name].get_value()
        else:
            def_opt = type(self)._opt_hash[opt_name].entry.get_value()

        cur_val = self.get_opt(opt_name, interpreted=False)
        try:
            return cur_val == def_opt or str(cur_val) == str(def_opt)
        except ValueError:
            return False

    @abc.abstractmethod
    def main(self, **kwargs):
        pass

    def __getattr__(self, item):
        if type(self)._opt_hash is not None and item in type(self)._opt_hash:
            return self.get_opt(item)
        else:
            raise AttributeError('Unknown attribute: {}'.format(item))

    def __setattr__(self, key, value):
        if type(self)._opt_hash is not None and key in type(self)._opt_hash:
            return self.set_opt(key, value)
        else:
            super(AbilityBase, self).__setattr__(key, value)

    def result(self):
        return self._ret_value

    def is_stopped(self):
        return not self._alive

    def _is_started(self):
        return self._started_status

    def howto(self):
        self._view.help('No howto was defined for this ability yet.')

    def _start_many(self, abl_lst):
        for abl in abl_lst:
            self.logger.debug('[{}] calling start'.format(
                abl._info.get_name())
            )
            abl.start()

    def _stop_many(self, abl_lst):
        for abl in abl_lst:
            self.logger.debug('[{}] calling stop'.format(abl._info.get_name()))
            abl.stop()

        for abl in abl_lst:
            self.logger.debug('[{}] joining'.format(abl._info.get_name()))
            abl.join()

    def _start_wait_and_stop(self, abl_lst):
        self._start_many(abl_lst)
        self._wait()
        self._stop_many(abl_lst)

    """ Emulate a thread/process (duck typing)
         __
     ___( o)>
     \ <_. )
      `---'
    """

    def start(self, *args, **kwargs):
        self._started_status = True
        self.logger.debug('[{}] - status is {}'.format(
            self._info.get_name(),
            self._started_status))
        try:
            self.logger.debug('[{}] - start of main'.format(
                self._info.get_name())
            )
            self._ret_value = self.main(*args, **kwargs)
            self.logger.debug('[{}] - end of main'.format(
                self._info.get_name())
            )
        finally:
            self._started_status = False
            self.logger.debug('[{}] - set status {} '.format(
                self._info.get_name(),
                self._started_status)
            )

    def stop(self):
        self._alive = False

    def join(self, timeout=0):
        """
        Timeout is here to keep the interface compatible
        stop it directly when an ability is not run into a thread (simple
        AbilityBase module)
        """
        self.stop()
