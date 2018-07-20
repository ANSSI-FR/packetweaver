import subprocess
import re


def get_local_net_conf(iface):
    """ Return the local machine IP (only IPv4 for now) and MAC addresses

    The information is gathered by parsing the output of
    the "ip a show <inet>" system command.
    """
    re_ip = r'.*inet\s(?P<ip>\d{1,3}(\.\d{1,3}){3}).*'
    re_mac = r'.*link/ether\s(?P<mac>[0-9a-f]{2}(?::[0-9a-f]{2}){5}).*'

    try:
        r = subprocess.check_output(
            ['ip', 'address', 'show', iface]
        ).replace('\n', ' ')
    except subprocess.CalledProcessError as e:
        raise ValueError('{}'.format(e))

    r_ip = re.match(re_ip, r)
    r_mac = re.match(re_mac, r, re.IGNORECASE)

    if r_ip and r_mac:
        return {'ip': r_ip.group('ip'), 'mac': r_mac.group('mac')}
    else:
        raise ValueError(
            'Could not extract ip/mac information from '
            'the "ip address show {}" command'.format(iface))


if __name__ == '__main__':
    try:
        print(get_local_net_conf('eno1'))
    except ValueError as e:
        print("{}".format(e))
