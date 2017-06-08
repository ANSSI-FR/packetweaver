# coding: utf8
from packetweaver.core.ns import *

try:
    import numpy
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class Ability(AbilityBase):
    _info = AbilityInfo(
        name='Detect leaks',
        description='Just a quick demo that when a module is missing, you can use this ability.'
    )

    _option_list = [

    ]


    @classmethod
    def check_preconditions(cls, module_factory):
        l = []
        if not HAS_NUMPY:
            l.append('Numpy support missing or broken. Please install Numpy or proceed to an update.')
        l += super(Ability, cls).check_preconditions(module_factory)
        return l

    def main(self):
        pass