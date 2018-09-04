from packetweaver.core import ns
import subprocess
import os


class Ability(ns.AbilityBase):
    _info = ns.AbilityInfo(
        name='Ping a target',
    )

    _option_list = [
        ns.IpOpt('ip_dst', default='8.8.8.8', comment='Ping Destination IP'),
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
