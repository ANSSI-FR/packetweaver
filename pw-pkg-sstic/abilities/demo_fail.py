from packetweaver.core import ns

try:
    import unknown
    HAS_UNKNOWN = True
except ImportError:
    HAS_UNKNOWN = False


class Ability(ns.AbilityBase):
    _info = ns.AbilityInfo(
        name='Detect leaks',
        description='Just a quick demo that when a module is missing, '
                    'you can use this ability.'
    )

    _option_list = [

    ]

    @classmethod
    def check_preconditions(cls, module_factory):
        l_dep = []
        if not HAS_UNKNOWN:
            l_dep.append('Numpy support missing or broken. '
                         'Please install Numpy or proceed to an update.')
        l_dep += super(Ability, cls).check_preconditions(module_factory)
        return l_dep

    def main(self):
        pass
