# coding: utf8
import random


class RandDraw(object):
    """ Generate random values for high level data """

    def __init__(self, rng):
        self._rng = rng

    def ipv4(self, expr='*.*.*.*'):
        """ Generate an random IPv4 address

        :param expr: str - a pattern example is '1-128.*.24-27.*'
        :return: str - a well formed IP address (not especially valid)
                 None or raise ValueError or ipaddress.AddressValueError if fail
        """
        # generate a random IP following the given expression
        expression = expr.replace(' ', '')
        l = expression.split('.')
        ip_l = []
        if len(l) != 4:
            print("Bad ipv4 expression - a correct pattern is '1-23.43.*.*'.")
            return None
        for n in l:
            inter = n.split('-')
            if len(inter) == 2:
                ip_num = "{}".format(self._rng.randint(int(inter[0]), int(inter[1])))
            elif len(inter) == 1:
                if inter[0] == "*":
                    ip_num = "{}".format(self._rng.randint(0, 255))
                elif inter:
                    ip_num = inter[0]
            else:
                print("Bad ipv4 expression items - a correct pattern is '1-23.43.*.*'.")
                return None
            ip_l.append(ip_num)

        # test pattern validity
        ip_str = u".".join(ip_l)
        return ip_str

    def ipv6(self):
        """ Generate a random IPv6 address

        Warning: expression is not yet supported

        :return: str - ipv6 valid address
        """
        # return ':'.join('{:x}'.format(random.randint(0, 2**16 - 1)) for i in xrange(8))
        randint = self._rng.randint(0, 2 ** 128 - 1)
        return ':'.join(
            [
                hex(
                    int((randint >> i) & 0xFFFF)
                )[2:]
                for i in range(0, 128, 16)
            ]
        )

    def string(self, size=0, values="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"):
        """ Return a random string

        :param size: length of the generated string. Let size to zero to have a random length string between 0 and 100
        :param values: characters to used to generate the string
        :return: string
        """
        if size:
            return "".join(values[self._rng.randint(0, len(values) - 1)] for i in range(size))
        return "".join(values[self._rng.randint(0, len(values) - 1)] for i in range(self._rng.randint(0, 100)))

    def number(self, lower_val=-10, higher_val=10):
        """ Generate a random number between two values

        make sure lower_val <= higher_val.
        if lower_val == higher_val, this value will always be returned

        :param lower_val: float/integer - low value of the interval
        :param higher_val: float/integer - high value of the interval
        """
        if isinstance(lower_val, float) or isinstance(higher_val, float):
            return self._rng.uniform(lower_val, higher_val)
        return self._rng.randint(lower_val, higher_val)

    def mac(self, expr='*:*:*:*:*:*'):
        """ Generate a random mac address following a pattern

        :param expr: pattern used to generate the address, e.g. '01:00:5e:00-7f:*:*'
        :return: string - mac address, 00:00:00:00:00:00 by default
        """
        expression = expr.replace(' ', '')
        l_mac = []
        for item in expression.split(':'):
            inter = item.split('-')
            if len(inter) == 2:
                i = self._rng.randint(int(inter[0], 16), int(inter[1], 16))
            elif len(inter) == 1:
                if inter[0] == '*':
                    i = self._rng.randint(0, 255)
                elif inter:
                    i = int(inter[0], 16)
                else:
                    print("Bad mac pattern")
            else:
                print("Bad mac expression")
                return None
            l_mac.append(i)
        return ':'.join('{:02x}'.format(item) for item in l_mac)
