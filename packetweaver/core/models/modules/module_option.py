import abc
import os
import re
import copy
import random
import packetweaver.libs.gen.rand_draw as draw
import packetweaver.libs.sys.ipaddress_mgmt as ipaddr_mgmt

try:
    import packetweaver.libs.gen.cyclic_rng as cyclic_rng
    HAS_CYCLIC_RNG = True
except ImportError:
    HAS_CYCLIC_RNG = False

# Activate pyroute2 associated function if available
try:
    import pyroute2

    HAS_PYROUTE2 = True
except ImportError:
    print('Cannot verify NIC interfaces existence! Please install pyroute2')
    HAS_PYROUTE2 = False


class ModuleOption(object):
    def __init__(self, name, default=None, comment=None, optional=False):
        """ Main class to define an parameter type for a module/ability

        :param name: name that the option will be called with
        :param value: value of the option
        :param comment: describe what the option is doing
        :param optional: define if the option must be specified to run the abl
        """
        self._name = name
        self._optional = optional
        assert (self.is_valid(default))
        self._default = default
        self._comment = comment

    def get_name(self):
        """ Return the option name """
        return self._name

    def get_value(self):
        """ Return directly the option value """
        return self._default

    def get_comment(self):
        """ Return the option description string """
        return self._comment

    def is_optional(self):
        """ Indicates if the option is optional for the ability to run """
        return self._optional

    def get_options_summary(self):
        return {
            'name': self.get_name(),
            'default': self.get_value(),
            'comment': self.get_comment(),
            'optional': self.is_optional(),
        }

    def is_valid(self, v):
        """ Check if a value is valid for the option type

        The check is performed only if the option in not optional

        :param v: value to check the validity
        """
        if not self.is_optional() and (v is None or v == 'None'):
            return False
        return True

    def generate_one_value(self, v):
        """ Equivalent at this class level to get_value() """
        assert (self.is_valid(v))
        return v


class ModuleOptionWithPossibleValues(ModuleOption):
    """ Option type for which a set of possible values has been predefined

    The predefined values are organized as a dict, where keys are this option
    possible values and the values of the dict are callable that return
    a "usable" value for Abilities
    """
    _possible_val = {}

    @abc.abstractmethod
    def __init__(self, name, default=None, comment=None, optional=False,
                 rng=draw.RandDraw(random)):
        super(ModuleOptionWithPossibleValues, self).__init__(name,
                                                             default=default,
                                                             comment=comment,
                                                             optional=optional)
        self._rng = rng

    @classmethod
    def get_possible_values(cls, typed=None, ref=None):
        """ List all the possible values, whose name starts with "typed"

        :param typed: beginning of the name of a possible value
                      (used for command line completion)
        """
        return [i for i in cls._possible_val.keys()
                if typed is None
                or i.startswith(typed)]

    def get_options_summary(self):
        return {
            'name': self.get_name(),
            'default': self.get_value(),
            'comment': self.get_comment(),
            'possible_values': '|'.join(type(self).get_possible_values()),
            'optional': self.is_optional(),
        }

    def generate_one_value(self, v):
        """ Return a valid value for the option, whether it be the interval
        value or a generated value by one of the callable associated to
        the possible values
        """
        assert (self.is_valid(v))

        if v is not None and 0 < len([v for pv in type(self)._possible_val
                                      if v.startswith(pv)]):
            return self._possible_val[v](self._rng)
        return v


class IpOpt(ModuleOptionWithPossibleValues):
    _possible_val = {
        'RandIP4': lambda rng: rng.ipv4(),
        'RandIP6': lambda rng: rng.ipv6(),
        'RandIP_classA': lambda rng: rng.ipv4('0-127.*.*.*'),
        'RandIP_classB': lambda rng: rng.ipv4('128-191.*.*.*'),
        'RandIP_classC': lambda rng: rng.ipv4('192-223.*.*.*'),
        'RandIP_classD': lambda rng: rng.ipv4('224-239.*.*.*'),
        'RandIP_classD_Multicast': lambda rng: rng.ipv4('224-239.*.*.*'),
        'RandIP_classE': lambda rng: rng.ipv4('240-255.*.*.*'),
        'RandIP_classE_Reserved': lambda rng: rng.ipv4('240-255.*.*.*'),
    }

    def __init__(self, name, default='RandIP4', comment=None, optional=False,
                 rng=draw.RandDraw(random)):
        """ Holds an IPv4 or an IPv6 address
        """
        super(IpOpt, self).__init__(name, default=default, comment=comment,
                                    optional=optional, rng=rng)

    def is_valid(self, v):
        return (
            (self.is_optional() and (v is None or v == 'None'))
            or ipaddr_mgmt.is_a_valid_ip_address(v)
            or 0 < len([v for pv in type(self)._possible_val
                        if v.startswith(pv)])
        )

    def generate_one_value(self, v):
        return super(IpOpt, self).generate_one_value(v)


class PrefixOpt(ModuleOption):
    def __init__(self, name, default='127.0.0.0/8', comment=None,
                 optional=False, ordered=False, rng_class=None):
        """ Holds an IPv4 or an IPv6 address
        """
        super(PrefixOpt, self).__init__(name, default=default, comment=comment,
                                        optional=optional)
        if HAS_CYCLIC_RNG and rng_class is None:
            self._rng_cls = cyclic_rng.CyclicPRNG
        else:
            self._rng_cls = rng_class
        self._ordered = ordered

    def iterate_over_a_prefix(self, prefix):
        ip_count_in_prefix = ipaddr_mgmt.get_ip_count_in_prefix(prefix)
        if HAS_CYCLIC_RNG and not self._ordered:
            iterator = self._rng_cls(ip_count_in_prefix + 1).get_random()
        else:
            iterator = iter(range(1, ip_count_in_prefix + 1))
        for i in iterator:
            yield ipaddr_mgmt.get_nth_ip_in_prefix(prefix, i)
        raise StopIteration()

    def is_valid(self, v):
        return ((v is None or v == 'None')
                and self.is_optional()) \
                or (ipaddr_mgmt.is_a_valid_prefix(v))

    def generate_one_value(self, v):
        return self.iterate_over_a_prefix(v)


class MacOpt(ModuleOptionWithPossibleValues):
    _possible_val = {
        'RandMac': lambda rng: rng.mac(),
        'RandMulticastMac': lambda rng: rng.mac('01:00:5e:00-7f:*:*'),
        'MacFF': lambda _: 'ff:ff:ff:ff:ff:ff',
        'Mac00': lambda _: '00:00:00:00:00:00',
    }
    _regexp_valid1 = re.compile(
        '^(?:(?:(?:[0-9a-f]{2})|(?:\\*)):){5}(?:(?:[0-9a-f]{2})|(?:\\*))$',
        re.I)
    _regexp_valid2 = re.compile('^[0-9a-f]{12}$', re.I)

    def __init__(self, name, default='RandMac', comment=None, optional=False,
                 rng=draw.RandDraw(random)):
        super(MacOpt, self).__init__(name, default=default, comment=comment,
                                     optional=optional, rng=rng)

    def is_valid(self, v):
        return (
            (self.is_optional() and (v is None or v == 'None'))
            or (
                isinstance(v, str) and (
                    type(self)._regexp_valid1.search(v) is not None
                    or type(self)._regexp_valid2.search(v) is not None
                    or 0 < len([v for pv in type(self)._possible_val
                                if v.startswith(pv)])
                )
            )
        )


class BoolOpt(ModuleOptionWithPossibleValues):
    _possible_val = {
        'True': lambda: 'True',
        'False': lambda: 'False'
    }

    def __init__(self, name, default=False, comment=None, optional=False):
        super(BoolOpt, self).__init__(name, default=default, comment=comment,
                                      optional=optional)

    def is_valid(self, v):
        return (
            (self.is_optional() and (v is None or v == 'None'))
            or isinstance(v, bool)
            or (isinstance(v, str) and v.lower() in ['true', 'false'])
        )

    def generate_one_value(self, v):
        if isinstance(v, type(None)):
            return None
        if isinstance(v, bool):
            return v
        if str(v).lower() == 'true':
            return True
        return False


class ChoiceOpt(ModuleOption):
    def __init__(self, name, choices, default=None, comment=None,
                 optional=False):
        if len(choices) == 0:
            raise ValueError(
                'Invalid choice list: choice list must be non-empty.'
            )

        self._possible_val = copy.deepcopy(choices)

        if not optional and default is None:
            super(ChoiceOpt, self).__init__(name, self._possible_val[0],
                                            comment, optional)
        else:
            super(ChoiceOpt, self).__init__(name, default, comment, optional)
            assert self.is_valid(default)

    def get_possible_values(self, typed=None, ref=None):
        l_val = copy.deepcopy(self._possible_val)
        return [i for i in l_val if typed is None or i.startswith(typed)]

    get_choices = get_possible_values

    def get_choices_onestring(self):
        return '|'.join(self._possible_val)

    def is_valid(self, v):
        return (
            (self.is_optional() and (v is None or v == 'None'))
            or v in self._possible_val
        )

    def get_options_summary(self):
        return {
            'name': self._name,
            'default': self.get_value(),
            'comment': self.get_comment(),
            'optional': self.is_optional(),
            'choices': self.get_choices_onestring()
        }

    def generate_one_value(self, s):
        """ Returns either None if the value is None and the field is optional,
         or the first choice if the value is None and the field is
         not optional. If the value is a valid choice, returns that choice.
        """
        if isinstance(s, type(None)):
            if self.is_optional():
                return None
            return self._possible_val[0]
        if s in self._possible_val:
            return s
        raise ValueError('Should never happen if is_valid is doing its job')


class StrOpt(ModuleOptionWithPossibleValues):
    _possible_val = {'RandString': lambda rng: rng.string(), }

    def __init__(self, name, default='RandString', comment=None,
                 optional=False, rng=draw.RandDraw(random)):
        """ Handles string type parameters """
        super(StrOpt, self).__init__(name, default=default, comment=comment,
                                     optional=optional, rng=rng)

    def is_valid(self, v):
        return (self.is_optional()
                and (v is None or v == 'None')) \
                or isinstance(v, str)


class NumOpt(ModuleOptionWithPossibleValues):
    _possible_val = {
        'RandByte': lambda rng: rng.number(0, 2**8-1),
        'RandShort': lambda rng: rng.number(0, 2**16-1),
        'RandInt': lambda rng: rng.number(0, 2**32-1),
        'RandLong': lambda rng: rng.number(0, 2**64-1),
        'RandSByte': lambda rng: rng.number(-2**7, 2**7-1),
        'RandSShort': lambda rng: rng.number(-2**15, 2**15-1),
        'RandSInt': lambda rng: rng.number(-2**31, 2**31-1),
        'RandSLong': lambda rng: rng.number(-2**63, 2**63-1),
    }

    def __init__(self, name, default='RandByte', comment=None, optional=False,
                 rng=draw.RandDraw(random)):
        """ Handles number parameters

        :param default: the number cast into a string
        """
        super(NumOpt, self).__init__(name, default=default, comment=comment,
                                     optional=optional, rng=rng)

    def is_valid(self, v):
        """ Validate that the input type can be casted to a number. """
        if self.is_optional() and (v is None or v == 'None'):
            return True
        try:
            v = int(v)
            ok = True
        except (ValueError, TypeError):
            try:
                # try float conversion
                v = float(v)
                ok = True
            except (ValueError, TypeError):
                ok = 0 < len([v for pv in type(self)._possible_val
                              if v.startswith(pv)])
        return ok

    def generate_one_value(self, s):
        accepted_types = (int, float)

        if isinstance(s, type(None)):
            return None
        elif isinstance(s, accepted_types):
            return s
        try:
            return int(s)
        except (ValueError, TypeError):
            try:
                # try float conversion
                return float(s)
            except (ValueError, TypeError):
                return super(NumOpt, self).generate_one_value(s)


class PortOpt(NumOpt):
    _possible_val = {
        'RandPort': lambda rng: rng.number(1, 65535),
        'RandPrivilegedPort': lambda rng: rng.number(1, 1024),
    }

    def __init__(self, name, default='RandPort', comment=None, optional=False,
                 rng=draw.RandDraw(random)):
        """ Contains a number being a valid port number """
        super(PortOpt, self).__init__(name, default=default, comment=comment,
                                      optional=optional, rng=rng)

    def is_valid(self, v):
        accepted_types = (int,)
        try:
            return (
                (self.is_optional() and (v is None or v == 'None'))
                or (isinstance(v, accepted_types) and 0 <= v <= 65535)
                or (
                    isinstance(v, str) or hasattr(v, '__str__')
                    and (
                        0 < len([v for pv in type(self)._possible_val
                                 if v.startswith(pv)])
                        or 0 <= int(str(v)) <= 65535
                    )
                )
            )
        except (ValueError, TypeError):
            return False


class NICOpt(ModuleOption):
    def __init__(self, name, default=None, comment=None, optional=False):
        super(NICOpt, self).__init__(name, default, comment, optional)

    def is_valid(self, v):
        if v is None:
            return True

        if not HAS_PYROUTE2:
            return True

        with pyroute2.IPDB() as ipdb:
            return v in ipdb.interfaces


class CallbackOpt(ModuleOption):
    def __init__(self, name, default=id, comment=None, optional=False):
        super(CallbackOpt, self).__init__(name, default, comment, optional)

    def is_valid(self, v):
        return ((v is None or v == 'None')
                and self.is_optional()) \
                or callable(v)


class PathOpt(StrOpt):
    def __init__(self, name, comment=None, optional=False,
                 executable=None, must_exist=None, readable=None,
                 writable=None, is_dir=False, **kwargs
                 ):
        """ Hold a path information

        Several options can put constraints on the specified file.
        TODO: implement constraints on folder

        :param name: option name
        :param default: a path suiting the file attribute arguments
        :param comment: explanations
        :param optional: if the parameter can be None
        :param executable: if true, the user running PacketWeaver must have
            execute privileges on the file. If false, the user running must NOT
            have execute privileges on the file. If None, it does not matter.
        :param must_exist: the file pointed must exist if True, must not exist
            if False, and existence does not matter if None.
        :param readable: if true, the user running PacketWeaver must have read
            privileges on the file. If false, the user running must NOT have
            read privileges on the file. If None, it does not matter.
        :param writable: if true, the user running PacketWeaver must have
            write privileges on the file. If false, the user running must NOT
            have write privileges on the file. If None, it does not matter.
        :param is_dir: the file is a directory
        """
        self._executable = executable
        self._must_exist = must_exist
        self._readable = readable
        self._writable = writable
        self._is_dir = is_dir
        if 'default' in kwargs:
            default = kwargs['default']
        else:
            if self._is_dir:
                default = os.getcwd()
            else:
                default = '/bin/true'

        super(PathOpt, self).__init__(name, default, comment, optional)

    def is_valid(self, v):
        if v is None or v == 'None':
            return self.is_optional()

        exists = os.access(v, os.F_OK)

        ret = (
            self._must_exist is None
            or not (self._must_exist ^ exists)
        )

        if self._is_dir:
            ret &= os.path.isdir(v)

        if self._executable is not None:
            exec_priv = os.access(v, os.X_OK)
            ret &= not (exec_priv ^ self._executable)

        if self._readable is not None:
            read_priv = os.access(v, os.R_OK)
            ret &= not (read_priv ^ self._readable)

        if self._writable is not None:
            write_priv = os.access(v, os.W_OK)
            ret &= not (write_priv & self._writable)

        return bool(ret)

    @classmethod
    def get_possible_values(cls, typed, ref=None):
        base_path = os.path.abspath(ref) if ref else os.getcwd()
        if len(typed) == 0:
            searched = base_path
            bs = ''
        else:
            searched = os.path.dirname(typed)
            if len(searched) == 0:
                searched = base_path
            bs = os.path.basename(typed)
        l_possible_val = [
            p + os.path.sep if os.path.isdir(os.path.join(searched, p)) else p
            for p in os.listdir(os.path.join(base_path, searched))
            if len(bs) == 0 or p.startswith(bs)
        ]
        return l_possible_val
