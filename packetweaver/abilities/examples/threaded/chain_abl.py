import packetweaver.core.ns as ns
from multiprocessing import Pipe


class Ability(ns.ThreadedAbilityBase):
    _info = ns.AbilityInfo(
        name='Chain abilities',
    )
    _dependencies = [
        ('abl_invert', 'base', 'Invert piped string'),
        ('abl_display', 'base', 'Display piped string')
    ]
    _option_list = [
        ns.StrOpt('msg', default='default', comment='Message to invert')
    ]

    def main(self, **kwargs):
        abl_inv = self.get_dependency('abl_invert')
        abl_disp = self.get_dependency('abl_display')

        # build communication channels
        to_abl, p_out = Pipe()
        abl_inv.add_in_pipe(p_out)
        abl_inv | abl_disp

        # run our controlled abilities
        self._view.debug('[main abl] Starting our two abilities')
        abl_inv.start()
        abl_disp.start()

        # ask to operate our message
        to_abl.send(self.msg)
        self._view.debug(
            '[main abl] Sending "{}" to be inverted'.format(self.msg)
        )

        # close all
        self._view.debug('[main abl] Hit ctrl+c to stop'.format(self.msg))
        self._wait()
        abl_inv.stop()
        abl_disp.stop()
        abl_inv.join()
        abl_disp.join()
        self._view.debug("[main abl] End")

    def howto(self):
        self._view.delimiter('Chain ability howto')
        self._view.info("""
        This ability invert and display its string input value. It is done
        using two abilities, one that invert the string, and another that
        display it.
        """)
