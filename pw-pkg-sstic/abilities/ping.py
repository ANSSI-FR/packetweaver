# coding: utf8
from packetweaver.core.ns import *
import subprocess
import os

class Ability(AbilityBase):
    _info = AbilityInfo(
        name='Ping a target',
    )

    _option_list = [
        IpOpt('ip_dst', '8.8.8.8', 'Ping Destination IP'),
    ]

    def main(self):
        cmd = '/bin/ping6' if self.ip_dst.find(':') != -1 else '/bin/ping'
        rc = subprocess.call(
            [cmd, '-c 1', '-w 1', self.ip_dst],
            stdout=os.open('/dev/null', os.O_WRONLY),
            stderr=os.open('/dev/null', os.O_WRONLY)
        )

        if rc == 0:
            self._view.success('{} is UP'.format(self.ip_dst))
        else:
            self._view.warning('{} is DOWN'.format(self.ip_dst))
